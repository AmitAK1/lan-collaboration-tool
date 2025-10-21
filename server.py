# server.py
import socket
import threading
import sys
import os
import time
import numpy as np
import pyaudio # New import

# Try to import opuslib, but make it optional
try:
    import opuslib
    OPUS_AVAILABLE = True
    print("[INFO] Opus codec available - using compressed audio")
except Exception as e:
    OPUS_AVAILABLE = False
    print(f"[INFO] Opus codec not available - using raw audio (install Opus library for better quality)")
    print(f"[DEBUG] Opus import error: {e}")

# --- Server Configuration ---
HOST = '172.17.57.20'  # Your server's IP
PORT = 6543
SERVER_FILES_DIR = "server_files"

# --- Audio/Video Configuration ---
UDP_PORT = 6544 # New port for audio/video
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 1024

# --- Client Management ---
clients = []
nicknames = []
server_running = True

# --- Audio/Video Client Management ---
audio_clients = {} # Maps nickname -> (ip, port)
latest_audio_chunks = {} # Maps (ip, port) -> audio_data
audio_lock = threading.Lock() # Lock for audio_clients and latest_audio_chunks
audio_decoders = {} # Maps (ip, port) -> opuslib.Decoder

# --- Presenter Management (from your Step 3) ---
current_presenter = None
presenter_lock = threading.Lock()

# --- (os.makedirs, broadcast, broadcast_all functions are identical) ---
os.makedirs(SERVER_FILES_DIR, exist_ok=True)
print(f"[INFO] Files will be stored in: {os.path.abspath(SERVER_FILES_DIR)}")

def broadcast(message, _sender_client):
    for client in clients:
        if client != _sender_client:
            try:
                client.send(message)
            except:
                remove_client(client)

def broadcast_all(message):
    for client in clients[:]:
        try:
            client.send(message)
        except:
            remove_client(client)

# --- NEW: UDP Broadcast Function ---
def broadcast_udp(data, _sender_addr, udp_socket):
    """
    Broadcasts UDP data to all registered clients except the sender.
    """
    with audio_lock:
        # Create a copy of addresses to broadcast to
        targets = [addr for addr in audio_clients.values() if addr != _sender_addr]
    
    for addr in targets:
        try:
            udp_socket.sendto(data, addr)
        except Exception as e:
            print(f"[AUDIO] Failed to send UDP to {addr}: {e}")

# --- MODIFIED: remove_client Function ---
def remove_client(client):
    """
    Removes a client from all lists and notifies others.
    """
    global current_presenter
    if client in clients:
        index = clients.index(client)
        nickname = nicknames[index]
        
        # Stop presenter if disconnecting
        with presenter_lock:
            if current_presenter == client:
                current_presenter = None
                print(f"[PRESENTER] {nickname} stopped presenting (disconnected).")
                broadcast_all("CMD:PRESENTER_SET:NONE\n".encode('utf-8'))
        
        # Remove from audio list
        with audio_lock:
            if nickname in audio_clients:
                addr = audio_clients.pop(nickname)
                latest_audio_chunks.pop(addr, None) # Remove any lingering chunk
                # --- NEW: Remove decoder ---
                audio_decoders.pop(addr, None)
                # --- End ---
                print(f"[AUDIO] Removed {nickname} from audio clients.")

        client.close()
        clients.remove(client)
        nicknames.remove(nickname)
        
        print(f"[DISCONNECT] {nickname} has left.")
        broadcast(f"[SERVER] {nickname} has left the chat.\n".encode('utf-8'), None)
        # --- NEW: Notify clients to remove user from UI ---
        broadcast_all(f"CMD:USER_LEFT:{nickname}\n".encode('utf-8'))
        # --- End of new code ---

# --- MODIFIED: handle_client Function ---
def handle_client(client):
    """
    Handles Chat, Files, and Screen Sharing commands.
    """
    global current_presenter
    
    # 1. Nickname setup
    nickname = None
    try:
        client.send('NICK'.encode('utf-8'))
        nickname = client.recv(1024).decode('utf-8').strip()
        
        if nickname in nicknames:
            client.send(f"ERROR:NICK_TAKEN:{nickname}\n".encode('utf-8'))
            client.close()
            return
        
        if not nickname:
            client.send("ERROR:NICK_EMPTY\n".encode('utf-8'))
            client.close()
            return
        
        nicknames.append(nickname)
        clients.append(client)
        
        print(f"[CONNECT] {nickname} has joined.")
        # --- FIX: Corrected utf-g to utf-8 ---
        broadcast(f"[SERVER] {nickname} joined the chat!\n".encode('utf-8'), client)
        client.send("[SERVER] Connected successfully.\n".encode('utf-8'))
        
        # Notify of existing files
        for filename in os.listdir(SERVER_FILES_DIR):
            filesize = os.path.getsize(os.path.join(SERVER_FILES_DIR, filename))
            client.send(f"CMD:FILE_NEW_AVAILABLE:Server:{filename}:{filesize}\n".encode('utf-8'))

        # Tell client the UDP port
        client.send(f"CMD:AUDIO_PORT:{UDP_PORT}\n".encode('utf-8'))

    except Exception as e:
        print(f"[ERROR] Failed nickname setup: {e}")
        if client in clients:
            index = clients.index(client)
            clients.remove(client)
            if index < len(nicknames):
                nicknames.pop(index)
        client.close()
        return

    # 3. Listen for messages (Main TCP Loop)
    while True:
        try:
            message_bytes = client.recv(1024)
            if not message_bytes:
                remove_client(client)
                break
                
            message = message_bytes.decode('utf-8').strip()
            
            # --- A. FILE UPLOAD (Your working code) ---
            if message.startswith('CMD:FILE_UPLOAD_START:'):
                try:
                    parts = message.split(':', 3)
                    filename = os.path.basename(parts[2])
                    filesize = int(parts[3])
                    filepath = os.path.join(SERVER_FILES_DIR, filename)
                    print(f"[FILE UPLOAD] {nickname} wants to upload {filename} ({filesize} bytes).")
                    client.send(f"CMD:FILE_READY_TO_RECV:{filename}\n".encode('utf-8')) # Added \n
                    bytes_received = 0
                    with open(filepath, 'wb') as f:
                        while bytes_received < filesize:
                            remaining = filesize - bytes_received
                            chunk_size = min(4096, remaining)
                            chunk = client.recv(chunk_size)
                            if not chunk: raise Exception("Client disconnected")
                            f.write(chunk)
                            bytes_received += len(chunk)
                    print(f"[FILE UPLOAD] ✓ Received {filename} from {nickname} successfully.")
                    broadcast(f"CMD:FILE_NEW_AVAILABLE:{nickname}:{filename}:{filesize}\n".encode('utf-8'), client)
                except Exception as e:
                    print(f"[ERROR] File upload failed: {e}")
                    client.send(f"[SERVER] Error uploading file: {e}\n".encode('utf-8'))

            # --- B. FILE DOWNLOAD (Your working code) ---
            elif message.startswith('CMD:FILE_DOWNLOAD_REQUEST:'):
                try:
                    filename = os.path.basename(message.split(':', 2)[2])
                    filepath = os.path.join(SERVER_FILES_DIR, filename)
                    if os.path.exists(filepath):
                        filesize = os.path.getsize(filepath)
                        print(f"[FILE DOWNLOAD] {nickname} requesting {filename} ({filesize} bytes).")
                        client.send(f"CMD:FILE_SEND_START:{filename}:{filesize}\n".encode('utf-8')) # Added \n
                        with open(filepath, 'rb') as f:
                            while (chunk := f.read(4096)):
                                client.send(chunk)
                        print(f"[FILE DOWNLOAD] ✓ Sent {filename} to {nickname} successfully.")
                    else:
                        client.send(f"[SERVER] Error: File '{filename}' not found.\n".encode('utf-8'))
                except Exception as e:
                    print(f"[ERROR] File download failed: {e}")

            # --- C. PRESENTER REQUEST (Your working code) ---
            elif message == 'CMD:PRESENTER_REQUEST':
                with presenter_lock:
                    if current_presenter is None:
                        current_presenter = client
                        presenter_nick = nicknames[clients.index(client)]
                        print(f"[PRESENTER] {presenter_nick} is now presenting.")
                        broadcast_all(f"CMD:PRESENTER_SET:{presenter_nick}\n".encode('utf-8'))
                    else:
                        client.send("[SERVER] Cannot start presenting, another user is active.\n".encode('utf-8'))

            # --- D. PRESENTER STOP (Your working code) ---
            elif message == 'CMD:PRESENTER_STOP':
                with presenter_lock:
                    if current_presenter == client:
                        current_presenter = None
                        print(f"[PRESENTER] {nickname} stopped presenting.")
                        broadcast_all("CMD:PRESENTER_SET:NONE\n".encode('utf-8'))
            
            # --- E. SCREEN DATA (Your working code) ---
            elif message.startswith('CMD:SCREEN_DATA:'):
                with presenter_lock:
                    if current_presenter == client:
                        try:
                            filesize = int(message.split(':', 2)[2])
                            image_data = b''
                            bytes_received = 0
                            while bytes_received < filesize:
                                remaining = filesize - bytes_received
                                chunk_size = min(4096, remaining)
                                chunk = client.recv(chunk_size)
                                if not chunk: raise Exception("Presenter disconnected")
                                image_data += chunk
                                bytes_received += len(chunk)
                            
                            broadcast(message_bytes, client) # Send header
                            broadcast(image_data, client)     # Send data
                        except Exception as e:
                            print(f"[ERROR] Screen data relay failed: {e}")
                            current_presenter = None
                            broadcast_all("CMD:PRESENTER_SET:NONE\n".encode('utf-8'))
            
            # --- NEW: REPORT USER ---
            elif message.startswith('CMD:REPORT_USER:'):
                try:
                    reported_nickname = message.split(':', 2)[2]
                    # Simple logging for now. In a real app, write to a file.
                    print(f"--- [REPORT LOG] ---\n  Reporter: {nickname}\n  Reported: {reported_nickname}\n  Timestamp: {time.ctime()}\n  --------------------")
                    
                    # Optional: Notify the reporter their action was logged
                    client.send(f"[SERVER] Report for {reported_nickname} has been logged.\n".encode('utf-8'))
                except Exception as e:
                    print(f"[ERROR] Failed to parse report command: {message} - {e}")
                    
            # --- F. CHAT MESSAGE ---
            else:
                message_to_broadcast = f"[{nickname}] {message}\n".encode('utf-8')
                print(f"[MESSAGE] {message_to_broadcast.decode('utf-8').strip()}")
                broadcast_all(message_to_broadcast)
            
        except Exception as e:
            print(f"[ERROR] {e}")
            remove_client(client)
            break

# --- MODIFIED: Audio/Video Receiver Thread ---
def audio_server_thread():
    """
    [THREAD] Listens for UDP packets, DECODES audio, relays video.
    """
    global audio_clients, latest_audio_chunks, audio_decoders # Add decoders
    
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.bind((HOST, UDP_PORT))
    print(f"[AV] UDP Audio/Video server listening on {HOST}:{UDP_PORT}")

    while server_running:
        try:
            data, addr = udp_socket.recvfrom(65536) # Large buffer for video
            
            # 1. Check for HELLO packet (Handshake)
            if data.startswith(b'HELLO:'):
                try:
                    nickname = data.decode('utf-8').split(':', 1)[1]
                    with audio_lock:
                        audio_clients[nickname] = addr
                        # --- NEW: Initialize decoder for this client ---
                        if OPUS_AVAILABLE and addr not in audio_decoders:
                            try:
                                audio_decoders[addr] = opuslib.Decoder(RATE, CHANNELS)
                            except Exception as e:
                                print(f"[AUDIO] Failed to create Opus decoder for {nickname}: {e}")
                        # --- End ---
                        
                        # Find the TCP client for this user
                        tcp_client = clients[nicknames.index(nickname)]
                        
                        # --- NEW: Tell new user about existing users ---
                        for nick in audio_clients.keys():
                            if nick != nickname:
                                # Send via reliable TCP
                                tcp_client.send(f"CMD:USER_JOINED:{nick}\n".encode('utf-8'))
                        
                        # --- NEW: Tell all *other* users about new user ---
                        # Send via reliable TCP
                        broadcast(f"CMD:USER_JOINED:{nickname}\n".encode('utf-8'), tcp_client)

                    print(f"[AV] Registered {nickname} from {addr}")
                except Exception as e:
                    print(f"[AV] Failed HELLO packet from {addr}: {e}")
                continue
            
            # Find sender's nickname (if registered)
            sender_nick = None
            with audio_lock:
                for nick, a in audio_clients.items():
                    if a == addr:
                        sender_nick = nick
                        break
            
            if not sender_nick:
                # print(f"[UDP] Unregistered packet from {addr}. Ignoring.")
                continue # Ignore packets from unknown sources

            # 2. Check for Video Packet
            if data.startswith(b'VID:'):
                # Relay this packet to all *other* clients
                # We add the sender's nickname so receivers know who's video it is
                video_packet = f"VID:{sender_nick}:".encode('utf-8') + data[4:]
                broadcast_udp(video_packet, addr, udp_socket)

            # 3. Check for Audio Packet (Decode it!)
            elif data.startswith(b'AUD:'):
                encoded_data = data[4:]
                
                # Try Opus decoding if available
                if OPUS_AVAILABLE:
                    decoder = audio_decoders.get(addr)
                    if decoder:
                        try:
                            # Decode the received Opus data into raw PCM bytes
                            decoded_data = decoder.decode(encoded_data, CHUNK)
                            with audio_lock:
                                # Store the *decoded* raw data for mixing
                                latest_audio_chunks[addr] = decoded_data
                        except Exception as e:
                            # Opus decode failed, treat as raw audio
                            # print(f"[AUDIO] Opus decode error from {addr}, using raw: {e}")
                            with audio_lock:
                                latest_audio_chunks[addr] = encoded_data
                    else:
                        # No decoder, treat as raw
                        with audio_lock:
                            latest_audio_chunks[addr] = encoded_data
                else:
                    # Opus not available, treat as raw audio
                    with audio_lock:
                        latest_audio_chunks[addr] = encoded_data

        except Exception as e:
            if server_running:
                print(f"[AV] UDP server error: {e}")

    udp_socket.close()
    # --- NEW: Clean up decoders ---
    with audio_lock:
        audio_decoders.clear()
    # --- End ---
    print("[AV] UDP server shut down.")

# --- (Audio Mixing & Broadcast Thread is identical to your Step 4) ---
def audio_broadcast_thread():
    """
    [THREAD] Mixes raw audio chunks and broadcasts raw audio periodically.
    Adds nickname header.
    """
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    while server_running:
        try:
            time.sleep(0.01) # ~20ms chunk interval, mix just before next
            
            with audio_lock:
                if not latest_audio_chunks:
                    continue # No audio to mix
                
                # Chunks are now raw PCM bytes
                chunks_with_addr = list(latest_audio_chunks.items())
                targets = list(audio_clients.items()) # Get (nick, addr) pairs
                latest_audio_chunks.clear()

            if not chunks_with_addr:
                continue

            # --- Audio Mixing (Works on raw PCM bytes) ---
            decoded_chunks = []
            chunk_senders = [] # Store nickname corresponding to each chunk

            with audio_lock: # Need lock to map addr back to nickname safely
                for addr, chunk in chunks_with_addr:
                    if len(chunk) == CHUNK * CHANNELS * 2: # Check raw size (2 bytes per sample)
                        decoded_chunks.append(np.frombuffer(chunk, dtype=np.int16))
                        # Find nickname for this addr
                        sender_nick = "Unknown"
                        for nick, a in audio_clients.items():
                            if a == addr:
                                sender_nick = nick
                                break
                        chunk_senders.append(sender_nick)

            if not decoded_chunks:
                continue
                
            # Mix using numpy (same logic as before)
            mixed_chunk_np = np.zeros(CHUNK * CHANNELS, dtype=np.float32)
            for chunk_np in decoded_chunks:
                mixed_chunk_np += chunk_np.astype(np.float32)
            
            mixed_chunk_np /= len(decoded_chunks)
            mixed_chunk_np = np.clip(mixed_chunk_np, -32768, 32767)
            mixed_data = mixed_chunk_np.astype(np.int16).tobytes()

            # --- Broadcast ---
            # Send raw mixed data prefixed by "AUD:<sender_nickname>:"
            # Note: This sends a mix containing potentially multiple people's audio,
            # but we'll just label it with the *first* sender in this batch for simplicity.
            # A more complex approach would be needed for perfect speaker attribution.
            if chunk_senders:
                header = f"AUD:{chunk_senders[0]}:".encode('utf-8')
                packet_to_send = header + mixed_data

                for nick, addr in targets:
                    udp_socket.sendto(packet_to_send, addr)
                
        except Exception as e:
            if server_running:
                print(f"[AUDIO] Mixing/Broadcast error: {e}")

    udp_socket.close()

# --- (shutdown_server is identical to your Step 4) ---
def shutdown_server(server):
    global server_running
    server_running = False
    print("\n[SHUTTING DOWN] Server is closing...")
    for client in clients[:]: 
        try:
            client.send("[SERVER] Server is shutting down.\n".encode('utf-8'))
            client.close()
        except: pass
    try:
        server.close()
    except: pass
    print("[SHUTDOWN COMPLETE] Server has stopped.")
    sys.exit(0)

# --- MODIFIED: start_server Function ---
def start_server():
    """
    Initializes the server, audio threads, and listens for TCP connections.
    """
    global server_running
    
    # Start Audio/Video Threads
    threading.Thread(target=audio_server_thread, daemon=True).start()
    # --- FIX: Corrected typo from auto_ to audio_ ---
    threading.Thread(target=audio_broadcast_thread, daemon=True).start()

    # (The rest of the function is identical to your code)
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 
    server.settimeout(1.0) 
    try:
        server.bind((HOST, PORT))
        server.listen(5)
        print(f"[LISTENING] TCP Server is listening on {HOST}:{PORT}")
        print("[INFO] Press Ctrl+C to stop the server")
        
        while server_running:
            try:
                client, address = server.accept()
                if not server_running:
                    client.close()
                    break
                print(f"[NEW CONNECTION] {address[0]}:{address[1]} connected.")
                thread = threading.Thread(target=handle_client, args=(client,))
                thread.daemon = True 
                thread.start()
            except socket.timeout:
                continue
            except OSError as e:
                if server_running: print(f"[ERROR] Socket error: {e}")
                break
    except KeyboardInterrupt:
        shutdown_server(server)
    except Exception as e:
        print(f"[ERROR] Failed to start server: {e}")
        shutdown_server(server)


if __name__ == "__main__":
    try:
        start_server()
    except KeyboardInterrupt:
        print("\n[INTERRUPTED] Server stopped by user.")
        sys.exit(0)