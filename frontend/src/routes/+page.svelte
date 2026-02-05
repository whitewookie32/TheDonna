<script>
	import { onMount, onDestroy } from 'svelte';
	
	// State
	let ws = null;
	let isConnected = false;
	let isRecording = false;
	let mediaRecorder = null;
	let audioContext = null;
	let audioQueue = [];
	let isPlaying = false;
	let status = 'Tap microphone to start';
	let messages = [];
	let wsUrl = 'wss://api.together.xyz/ws'; // Will be replaced with actual backend URL
	
	// Audio recording
	let audioChunks = [];
	let silenceTimer = null;
	let analyser = null;
	let silenceThreshold = 0.01;
	let silenceDuration = 1500; // ms
	
	onMount(() => {
		connectWebSocket();
		return () => {
			disconnectWebSocket();
		};
	});
	
	function connectWebSocket() {
		status = 'Connecting...';
		
		// Get WebSocket URL - auto-detect in production
		let backendUrl;
		if (import.meta.env.VITE_BACKEND_URL) {
			backendUrl = import.meta.env.VITE_BACKEND_URL;
		} else if (window.location.hostname === 'localhost') {
			backendUrl = 'ws://localhost:8000';
		} else {
			// Production: use same host with wss://
			backendUrl = `wss://${window.location.host}`;
		}
		console.log('Connecting to WebSocket:', backendUrl);
		ws = new WebSocket(`${backendUrl}/ws`);
		
		ws.onopen = () => {
			isConnected = true;
			status = 'Connected. Tap mic to speak';
			console.log('WebSocket connected');
		};
		
		ws.onmessage = async (event) => {
			const data = JSON.parse(event.data);
			console.log('Received:', data);
			
			switch(data.type) {
				case 'chunk_received':
					status = 'Listening...';
					break;
					
				case 'status':
					status = data.message;
					break;
					
				case 'transcript':
					messages = [...messages, { role: 'user', text: data.text }];
					break;
					
				case 'response_text':
					messages = [...messages, { role: 'donna', text: data.text }];
					break;
					
				case 'audio_response':
					await playAudio(data.audio);
					break;
					
				case 'error':
					console.error('Error:', data.message);
					status = `Error: ${data.message}`;
					isRecording = false;
					break;
					
				case 'pong':
					// Keepalive response
					break;
			}
		};
		
		ws.onerror = (error) => {
			console.error('WebSocket error:', error);
			isConnected = false;
			status = 'Connection error. Retrying...';
		};
		
		ws.onclose = () => {
			isConnected = false;
			status = 'Disconnected. Reconnecting...';
			// Attempt reconnect after 3 seconds
			setTimeout(connectWebSocket, 3000);
		};
	}
	
	function disconnectWebSocket() {
		if (ws) {
			ws.close();
			ws = null;
		}
	}
	
	async function toggleRecording() {
		if (isRecording) {
			await stopRecording();
		} else {
			await startRecording();
		}
	}
	
	async function startRecording() {
		try {
			const stream = await navigator.mediaDevices.getUserMedia({ 
				audio: {
					echoCancellation: true,
					noiseSuppression: true,
					sampleRate: 16000
				}
			});
			
			// Set up audio context for silence detection
			audioContext = new AudioContext({ sampleRate: 16000 });
			const source = audioContext.createMediaStreamSource(stream);
			analyser = audioContext.createAnalyser();
			analyser.fftSize = 256;
			source.connect(analyser);
			
			// Set up MediaRecorder
			mediaRecorder = new MediaRecorder(stream, {
				mimeType: 'audio/webm;codecs=opus'
			});
			
			audioChunks = [];
			
			mediaRecorder.ondataavailable = (event) => {
				if (event.data.size > 0) {
					audioChunks.push(event.data);
					// Send chunk to server
					sendAudioChunk(event.data);
				}
			};
			
			mediaRecorder.start(200); // Collect data every 200ms
			isRecording = true;
			status = 'Listening... (tap to stop)';
			
			// Start silence detection
			detectSilence();
			
		} catch (err) {
			console.error('Error accessing microphone:', err);
			status = 'Microphone access denied';
		}
	}
	
	function detectSilence() {
		if (!isRecording || !analyser) return;
		
		const dataArray = new Uint8Array(analyser.frequencyBinCount);
		analyser.getByteTimeDomainData(dataArray);
		
		// Calculate volume
		let sum = 0;
		for (let i = 0; i < dataArray.length; i++) {
			const value = (dataArray[i] - 128) / 128;
			sum += value * value;
		}
		const volume = Math.sqrt(sum / dataArray.length);
		
		if (volume < silenceThreshold) {
			if (!silenceTimer) {
				silenceTimer = setTimeout(() => {
					// Silence detected for threshold duration
					console.log('Silence detected, stopping recording');
					stopRecording();
				}, silenceDuration);
			}
		} else {
			if (silenceTimer) {
				clearTimeout(silenceTimer);
				silenceTimer = null;
			}
		}
		
		if (isRecording) {
			requestAnimationFrame(detectSilence);
		}
	}
	
	async function stopRecording() {
		if (mediaRecorder && mediaRecorder.state !== 'inactive') {
			mediaRecorder.stop();
		}
		
		// Stop all tracks
		if (mediaRecorder && mediaRecorder.stream) {
			mediaRecorder.stream.getTracks().forEach(track => track.stop());
		}
		
		if (audioContext) {
			audioContext.close();
			audioContext = null;
		}
		
		if (silenceTimer) {
			clearTimeout(silenceTimer);
			silenceTimer = null;
		}
		
		isRecording = false;
		status = 'Processing...';
		
		// Send end of utterance signal
		if (ws && ws.readyState === WebSocket.OPEN) {
			ws.send(JSON.stringify({ type: 'end_utterance' }));
		}
	}
	
	async function sendAudioChunk(blob) {
		if (!ws || ws.readyState !== WebSocket.OPEN) return;
		
		const reader = new FileReader();
		reader.onloadend = () => {
			const base64 = reader.result.split(',')[1];
			ws.send(JSON.stringify({
				type: 'audio_chunk',
				data: base64
			}));
		};
		reader.readAsDataURL(blob);
	}
	
	async function playAudio(base64Audio) {
		const audioData = Uint8Array.from(atob(base64Audio), c => c.charCodeAt(0));
		const blob = new Blob([audioData], { type: 'audio/mp3' });
		const url = URL.createObjectURL(blob);
		
		const audio = new Audio(url);
		audioQueue.push(audio);
		
		if (!isPlaying) {
			playNextAudio();
		}
	}
	
	async function playNextAudio() {
		if (audioQueue.length === 0) {
			isPlaying = false;
			status = isConnected ? 'Tap microphone to start' : 'Connecting...';
			return;
		}
		
		isPlaying = true;
		const audio = audioQueue.shift();
		status = 'Donna is speaking...';
		
		audio.onended = () => {
			URL.revokeObjectURL(audio.src);
			playNextAudio();
		};
		
		audio.onerror = (err) => {
			console.error('Audio playback error:', err);
			playNextAudio();
		};
		
		await audio.play();
	}
	
	// Keepalive ping
	setInterval(() => {
		if (ws && ws.readyState === WebSocket.OPEN) {
			ws.send(JSON.stringify({ type: 'ping' }));
		}
	}, 30000);
</script>

<svelte:head>
	<title>The Donna - Voice Assistant</title>
</svelte:head>

<div class="connection-status {isConnected ? 'connected' : 'disconnected'}">
	{isConnected ? 'Connected' : 'Disconnected'}
</div>

<h1>The Donna</h1>
<p class="subtitle">Your Executive Assistant</p>

<div class="voice-container">
	<button 
		class="mic-button {isRecording ? 'recording' : ''}" 
		on:click={toggleRecording}
		disabled={!isConnected}
	>
		{#if isRecording}
			⏹
		{:else}
			🎤
		{/if}
	</button>
	
	<p class="status {isRecording ? 'recording' : ''}">{status}</p>
	
	<div class="conversation">
		{#each messages as message}
			<div class="message {message.role}">
				{message.text}
			</div>
		{/each}
	</div>
</div>