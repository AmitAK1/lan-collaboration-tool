# client.py
import socket
import threading
import tkinter as tk
from tkinter import scrolledtext, simpledialog, messagebox, filedialog, ttk
import os
import time
import mss
from PIL import Image, ImageTk
import io
import pyaudio
import numpy as np
import cv2 # New import

# Try to import opuslib, but make it optional
try:
    import opuslib
    OPUS_AVAILABLE = True
except Exception:
    OPUS_AVAILABLE = False
    print("[INFO] Opus codec not available - using raw audio")

# --- Audio Configuration ---
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 1024

class ChatClient:
    def __init__(self):
        # --- (All state from Step 4) ---
        self.HOST = simpledialog.askstring("Server IP", "Enter Server IP:", initialvalue="172.17.57.20") # Use your IP
        if not self.HOST: exit()
        self.PORT = 6543
        
        self.NICKNAME = None
        self.client_socket = None
        
        if not self.connect_to_server():
            exit() 

        self.socket_lock = threading.Lock() 
        self.available_files = {}
        self.pending_upload = None
        self.downloading = False
        self.connected = True
        self.is_presenting = False
        self.presenter_thread = None
        self.screen_view_window = None
        self.screen_view_label = None
        self.audio_running = False
        self.is_muted = False
        self.udp_socket = None
        self.server_udp_addr = None # (host, port)
        self.p_audio = pyaudio.PyAudio()
        self.mic_stream = None
        self.speaker_stream = None
        
        # --- Opus Codec State ---
        self.opus_encoder = None
        self.opus_decoder = None
        # Add a dictionary to store decoders for other users
        self.peer_opus_decoders = {}
        # --- End of Opus state ---
        
        # --- NEW: Video State ---
        self.is_video_on = False
        self.video_send_thread = None
        self.video_window = None # Toplevel window for video grid
        self.video_feeds = {} # Maps nickname -> tk.Label
        self.video_capture = None # Our own webcam
        # --- End of new state ---

        # --- Build the GUI ---
        self.build_gui()
        
        # --- Start receive thread (identical) ---
        self.receive_thread = threading.Thread(target=self.receive_handler)
        self.receive_thread.daemon = True
        self.receive_thread.start()
    
    # --- (connect_to_server is identical to your Step 4) ---
    def connect_to_server(self):
        max_attempts = 5
        for attempt in range(max_attempts):
            if attempt == 0:
                self.NICKNAME = simpledialog.askstring("Nickname", "Enter your nickname:")
            else:
                self.NICKNAME = simpledialog.askstring("Nickname", 
                    f"Username taken! Please choose a different nickname:\n(Attempt {attempt + 1}/{max_attempts})")
            
            if not self.NICKNAME:
                messagebox.showinfo("Cancelled", "Connection cancelled by user.")
                return False
            
            try:
                if self.client_socket:
                    try: self.client_socket.close()
                    except: pass
                
                self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.client_socket.connect((self.HOST, self.PORT))
                server_cmd = self.client_socket.recv(1024).decode('utf-8').strip()
                if server_cmd != 'NICK':
                    messagebox.showerror("Protocol Error", f"Unexpected server response: {server_cmd}")
                    return False
                self.client_socket.send(self.NICKNAME.encode('utf-8'))
                response = self.client_socket.recv(1024).decode('utf-8').strip()
                if response.startswith('ERROR:NICK_TAKEN:'):
                    print(f"Username '{self.NICKNAME}' is already taken. Retrying...")
                    self.client_socket.close()
                    continue
                elif response.startswith('ERROR:NICK_EMPTY'):
                    messagebox.showwarning("Empty Username", "Username cannot be empty!")
                    self.client_socket.close()
                    continue
                elif response.startswith('[SERVER]'):
                    print(f"Successfully connected as '{self.NICKNAME}'")
                    self.welcome_message = response
                    return True
                else:
                    print(f"Unexpected response: {response}")
                    self.welcome_message = response
                    return True
            except Exception as e:
                messagebox.showerror("Connection Error", f"Failed to connect to server {self.HOST}:{self.PORT}\n{e}")
                return False
        messagebox.showerror("Connection Failed", f"Failed to connect after {max_attempts} attempts.")
        return False

    # --- MODIFIED: build_gui Function ---
    def build_gui(self):
        """
        Builds the GUI components, now with a Treeview for files.
        """
        self.window = tk.Tk()
        self.window.title(f"LAN Collab - ({self.NICKNAME})")
        self.window.geometry("700x600") # Made window a bit wider for columns

        # --- Main layout frames ---
        self.top_frame = tk.Frame(self.window)
        self.top_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.bottom_frame = tk.Frame(self.window)
        self.bottom_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        # --- Chat Display Area ---
        self.chat_area = scrolledtext.ScrolledText(self.top_frame, wrap=tk.WORD, width=50, height=20)
        self.chat_area.config(state=tk.DISABLED)
        self.chat_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        # --- Right-side panel for files and controls ---
        self.controls_frame = tk.Frame(self.top_frame, width=250)
        self.controls_frame.pack(side=tk.RIGHT, fill=tk.Y)
        
        tk.Label(self.controls_frame, text="Available Files:", font=("Helvetica", 10, "bold")).pack(anchor='w')
        
        # --- NEW: Treeview for Files ---
        tree_frame = tk.Frame(self.controls_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        self.file_tree = ttk.Treeview(tree_frame, columns=("name", "size", "sender"), show="headings", height=15)
        self.file_tree.heading("name", text="Filename")
        self.file_tree.heading("size", text="Size")
        self.file_tree.heading("sender", text="Sender")

        self.file_tree.column("name", width=120)
        self.file_tree.column("size", width=70, anchor='e') # 'e' for East (right align)
        self.file_tree.column("sender", width=80)
        
        # Add a scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.file_tree.yview)
        self.file_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.file_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        # --- End of Treeview ---
        
        self.download_button = tk.Button(self.controls_frame, text="Download Selected", command=self.request_download)
        self.download_button.pack(fill=tk.X, pady=5)
        
        self.send_file_button = tk.Button(self.controls_frame, text="Send File", command=self.select_file)
        self.send_file_button.pack(fill=tk.X)

        self.present_button = tk.Button(self.controls_frame, text="Start Presenting", command=self.toggle_presenting, bg="green", fg="white")
        self.present_button.pack(fill=tk.X, pady=(10, 0))

        self.mute_button = tk.Button(self.controls_frame, text="Mute", command=self.toggle_mute, bg="yellow", fg="black")
        self.mute_button.pack(fill=tk.X, pady=(5, 0))

        self.video_button = tk.Button(self.controls_frame, text="Start Video", command=self.toggle_video, bg="blue", fg="white")
        self.video_button.pack(fill=tk.X, pady=(5, 0))

        # --- (Status, Progress, Message Entry are the same) ---
        self.status_label = tk.Label(self.window, text="Ready", font=("Helvetica", 9), fg="green", anchor='w')
        self.status_label.pack(fill=tk.X, padx=10, pady=(5, 0))
        self.progress_bar = ttk.Progressbar(self.window, orient='horizontal', mode='determinate')
        self.progress_bar.pack(fill=tk.X, padx=10, pady=(0, 5))
        self.msg_entry = tk.Entry(self.bottom_frame, font=("Helvetica", 11))
        self.msg_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=5)
        self.send_button = tk.Button(self.bottom_frame, text="Send", command=self.send_message, width=10)
        self.send_button.pack(side=tk.RIGHT, padx=(5, 0))
        
        self.window.bind('<Return>', lambda event: self.send_message())
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    # --- (display_message, _update_chat_area, safe_ui_update are identical) ---
    def display_message(self, message):
        self.chat_area.config(state=tk.NORMAL)
        self.chat_area.insert(tk.END, message)
        self.chat_area.see(tk.END)
        self.chat_area.config(state=tk.DISABLED)

    def _update_chat_area(self, message):
        self.display_message(message)

    def safe_ui_update(self, func, *args, **kwargs):
        self.window.after(0, lambda: func(*args, **kwargs))
        
    # --- (send_with_lock, send_message identical to your Step 4) ---
    def send_with_lock(self, data):
        try:
            with self.socket_lock:
                self.client_socket.sendall(data)
        except Exception as e:
            self.connected = False
            self.safe_ui_update(self.display_message, f"[SYSTEM] Connection lost: {e}\n")
    
    def send_message(self):
        message = self.msg_entry.get()
        if message:
            if not self.connected:
                self.safe_ui_update(self.display_message, "[SYSTEM] Not connected.\n")
                return
            try:
                self.client_socket.send(message.encode('utf-8'))
                self.msg_entry.delete(0, tk.END)
            except Exception as e:
                self.connected = False
                self.safe_ui_update(self.display_message, f"[SYSTEM] Connection lost: {e}\n")

    # --- MODIFIED: on_closing Function ---
    def on_closing(self):
        self.connected = False
        self.audio_running = False
        self.is_video_on = False # --- NEW
        
        try: self.client_socket.send("".encode('utf-8'))
        except: pass
        try: self.client_socket.close()
        except: pass
        
        try:
            if self.udp_socket: self.udp_socket.close()
            if self.mic_stream: self.mic_stream.stop_stream(); self.mic_stream.close()
            if self.speaker_stream: self.speaker_stream.stop_stream(); self.speaker_stream.close()
            self.p_audio.terminate()
            if self.video_capture: self.video_capture.release() # --- NEW
        except Exception as e:
            print(f"Error closing resources: {e}")

        self.window.destroy()

    # --- (All File functions: select_file, upload_file_thread, request_download... are identical to your Step 4) ---
    def select_file(self):
        if not self.connected:
            messagebox.showerror("Not Connected", "Not connected to server.")
            return
        if self.is_presenting or self.screen_view_window:
            messagebox.showwarning("Busy", "Cannot send files while presenting or viewing.")
            return
            
        filepath = filedialog.askopenfilename()
        if not filepath: return
        filesize = os.path.getsize(filepath)
        basename = os.path.basename(filepath)
        self.pending_upload = (filepath, basename)
        try:
            self.client_socket.send(f"CMD:FILE_UPLOAD_START:{basename}:{filesize}".encode('utf-8'))
            self.safe_ui_update(self.display_message, f"[SYSTEM] Requesting to send {basename}...\n")
            self.safe_ui_update(self.send_file_button.config, state=tk.DISABLED)
        except Exception as e:
            self.connected = False
            self.safe_ui_update(self.display_message, f"[SYSTEM] Failed to send file request: {e}\n")

    def upload_file_thread(self, filepath, basename):
        try:
            filesize = os.path.getsize(filepath)
            self.safe_ui_update(self.status_label.config, text=f"Uploading: {basename}", fg="blue")
            bytes_sent = 0
            with self.socket_lock:
                with open(filepath, 'rb') as f:
                    while (chunk := f.read(4096)):
                        self.client_socket.send(chunk)
                        bytes_sent += len(chunk)
                        progress = (bytes_sent / filesize) * 100
                        self.safe_ui_update(self.progress_bar.config, value=progress)
                        self.safe_ui_update(self.status_label.config, 
                                          text=f"Uploading: {basename} - {int(progress)}%")
            self.safe_ui_update(self.status_label.config, text="Upload complete!", fg="green")
            self.safe_ui_update(self.display_message, f"[SYSTEM] ✓ Upload complete for {basename}.\n")
        except Exception as e:
            self.safe_ui_update(self.status_label.config, text="Upload failed!", fg="red")
            self.safe_ui_update(self.display_message, f"[SYSTEM] ✗ Upload failed: {e}\n")
        finally:
            self.pending_upload = None
            self.safe_ui_update(self.send_file_button.config, state=tk.NORMAL)
            self.window.after(3000, lambda: self.status_label.config(text="Ready", fg="green"))
            self.window.after(3000, lambda: self.progress_bar.config(value=0))
            
    def request_download(self):
        if not self.connected:
            messagebox.showerror("Not Connected", "Not connected to server.")
            return
        # Add other checks from your debugged code
        if self.is_presenting or self.screen_view_window or self.downloading:
            messagebox.showwarning("Busy", "Cannot download while another operation is in progress.")
            return
            
        try:
            # --- Get selected item from Treeview ---
            selected_item_iid = self.file_tree.focus()
            if not selected_item_iid:
                messagebox.showinfo("No Selection", "Please select a file from the list to download.")
                return
            
            # The filename is the iid we used when inserting
            filename = selected_item_iid
            # --- End of Treeview specific code ---
            
            self.client_socket.send(f"CMD:FILE_DOWNLOAD_REQUEST:{filename}".encode('utf-8'))
            self.safe_ui_update(self.download_button.config, state=tk.DISABLED)
            self.downloading = True

        except Exception as e:
            self.connected = False
            self.safe_ui_update(self.display_message, f"[SYSTEM] Download request failed: {e}\n")

    def download_file_inline(self, save_path, filesize):
        try:
            filename = os.path.basename(save_path)
            self.safe_ui_update(self.status_label.config, text=f"Downloading: {filename}", fg="blue")
            bytes_received = 0
            with open(save_path, 'wb') as f:
                while bytes_received < filesize:
                    remaining = filesize - bytes_received
                    chunk_size = min(4096, remaining)
                    chunk = self.client_socket.recv(chunk_size)
                    if not chunk: raise Exception("Server disconnected")
                    f.write(chunk)
                    bytes_received += len(chunk)
                    progress = (bytes_received / filesize) * 100
                    self.safe_ui_update(self.progress_bar.config, value=progress)
                    self.safe_ui_update(self.status_label.config, 
                                        text=f"Downloading: {filename} - {int(progress)}%")
            self.safe_ui_update(self.status_label.config, text="Download complete!", fg="green")
            self.safe_ui_update(self.display_message, f"[SYSTEM] ✓ Download complete: {filename}\n")
        except Exception as e:
            self.safe_ui_update(self.status_label.config, text="Download failed!", fg="red")
            self.safe_ui_update(self.display_message, f"[SYSTEM] ✗ Download failed: {e}\n")
        finally:
            self.downloading = False
            self.safe_ui_update(self.download_button.config, state=tk.NORMAL)
            self.window.after(3000, lambda: self.status_label.config(text="Ready", fg="green"))
            self.window.after(3000, lambda: self.progress_bar.config(value=0))
            
    # --- (All Screen Share functions are identical to your Step 4) ---
    def toggle_presenting(self):
        if not self.connected:
            messagebox.showerror("Not Connected", "Not connected to server.")
            return
        if self.is_presenting:
            self.send_with_lock("CMD:PRESENTER_STOP\n".encode('utf-8')) # Added \n
        else:
            if self.downloading or self.screen_view_window:
                messagebox.showwarning("Busy", "Cannot present while downloading or viewing.")
                return
            self.send_with_lock("CMD:PRESENTER_REQUEST\n".encode('utf-8')) # Added \n
            
    def start_sharing_thread(self):
        if self.presenter_thread is None or not self.presenter_thread.is_alive():
            self.is_presenting = True
            self.presenter_thread = threading.Thread(target=self.screen_share_loop, daemon=True)
            self.presenter_thread.start()
            self.safe_ui_update(self.status_label.config, text="You are presenting!", fg="blue")
            self.safe_ui_update(self.present_button.config, text="Stop Presenting", bg="red")

    def stop_sharing_thread(self):
        self.is_presenting = False
        self.safe_ui_update(self.status_label.config, text="Ready", fg="green")
        self.safe_ui_update(self.present_button.config, text="Start Presenting", bg="green")

    def screen_share_loop(self):
        with mss.mss() as sct:
            monitor = sct.monitors[1] 
            while self.is_presenting:
                try:
                    sct_img = sct.grab(monitor)
                    img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
                    img.thumbnail((1280, 720)) 
                    with io.BytesIO() as output:
                        img.save(output, format='JPEG', quality=75)
                        data = output.getvalue()
                    
                    header = f"CMD:SCREEN_DATA:{len(data)}\n".encode('utf-8')
                    with self.socket_lock:
                        self.client_socket.sendall(header)
                        self.client_socket.sendall(data)
                        
                    time.sleep(0.1) # 10 FPS
                except Exception as e:
                    if self.is_presenting: print(f"[ERROR] Screen share loop failed: {e}")
                    break
        print("[PRESENTER] Share thread stopped.")
        
    def show_screen_view_window(self):
        if self.screen_view_window is not None: return
        self.screen_view_window = tk.Toplevel(self.window)
        self.screen_view_window.title("Presentation View")
        self.screen_view_window.geometry("800x600")
        self.screen_view_label = tk.Label(self.screen_view_window)
        self.screen_view_label.pack(fill=tk.BOTH, expand=True)
        self.screen_view_window.protocol("WM_DELETE_WINDOW", self.hide_screen_view_window)

    def hide_screen_view_window(self):
        if self.screen_view_window:
            self.screen_view_window.destroy()
            self.screen_view_window = None
            self.screen_view_label = None

    def update_screen_view(self, image_data):
        if self.screen_view_window is None: return
        try:
            img = Image.open(io.BytesIO(image_data))
            win_width = self.screen_view_window.winfo_width()
            win_height = self.screen_view_window.winfo_height()
            if win_width > 1 and win_height > 1:
                img.thumbnail((win_width, win_height))
            photo = ImageTk.PhotoImage(img)
            self.screen_view_label.config(image=photo)
            self.screen_view_label.image = photo
        except Exception as e:
            print(f"[ERROR] Failed to update screen view: {e}")

    # --- (Audio functions: toggle_mute, init_audio are identical to Step 4) ---
    def toggle_mute(self):
        self.is_muted = not self.is_muted
        if self.is_muted:
            self.safe_ui_update(self.mute_button.config, text="Unmute", bg="red")
        else:
            self.safe_ui_update(self.mute_button.config, text="Mute", bg="yellow")
            
    def init_audio(self, port):
        """Called by receive_handler to start all audio systems."""
        try:
            self.server_udp_addr = (self.HOST, int(port))
            self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            
            self.mic_stream = self.p_audio.open(
                format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
            
            self.speaker_stream = self.p_audio.open(
                format=FORMAT, channels=CHANNELS, rate=RATE, output=True, frames_per_buffer=CHUNK)
            
            # Initialize Opus encoder and decoder
            if OPUS_AVAILABLE:
                try:
                    self.opus_encoder = opuslib.Encoder(RATE, CHANNELS, opuslib.APPLICATION_VOIP)
                    self.opus_decoder = opuslib.Decoder(RATE, CHANNELS)
                    print("[AUDIO] Opus encoder/decoder initialized.")
                except Exception as e:
                    print(f"[AUDIO] Failed to initialize Opus: {e}")
                    print("[AUDIO] Continuing with raw audio...")
                    self.opus_encoder = None
                    self.opus_decoder = None
            else:
                print("[AUDIO] Using raw audio (Opus not available)")
            
            self.audio_running = True
            
            threading.Thread(target=self.audio_send_thread, daemon=True).start()
            threading.Thread(target=self.audio_receive_thread, daemon=True).start()
            
            self.udp_socket.sendto(f'HELLO:{self.NICKNAME}'.encode('utf-8'), self.server_udp_addr)
            
            print(f"[AUDIO] Audio initialized for UDP port {port}")
            self.safe_ui_update(self.display_message, "[SYSTEM] Audio connected.\n")
            
        except Exception as e:
            print(f"[AUDIO] Failed to initialize audio: {e}")
            self.safe_ui_update(self.display_message, f"[SYSTEM] Audio failed to start: {e}\n")

    # --- MODIFIED: audio_send_thread ---
    def audio_send_thread(self):
        """[THREAD] Reads from mic, ENCODES, and sends via UDP with AUD: header."""
        opus_frame_size = CHUNK # Opus works well with common chunk sizes
        while self.audio_running:
            try:
                if self.is_muted:
                    # Read mic data even if muted to keep timing, but don't send real data
                    _ = self.mic_stream.read(opus_frame_size, exception_on_overflow=False)
                    # Create silence IN THE CORRECT FORMAT (int16 numpy array)
                    silent_frame = np.zeros(opus_frame_size * CHANNELS, dtype=np.int16)
                    raw_data = silent_frame.tobytes() # Convert numpy silence to bytes
                else:
                    # Read raw audio data (bytes)
                    raw_data = self.mic_stream.read(opus_frame_size, exception_on_overflow=False)

                if self.opus_encoder:
                    # Encode the raw audio bytes
                    encoded_data = self.opus_encoder.encode(raw_data, opus_frame_size)
                    # Send encoded data with header
                    self.udp_socket.sendto(b'AUD:' + encoded_data, self.server_udp_addr)
                else: # Fallback if encoder failed
                    self.udp_socket.sendto(b'AUD:' + raw_data, self.server_udp_addr)

            # Add a small sleep to prevent high CPU usage if mic read is too fast
            except BlockingIOError:
                time.sleep(0.005) # Wait briefly if no data available
            except Exception as e:
                if self.audio_running:
                    print(f"[AUDIO] Send error: {e}")
                break
        print("[AUDIO] Send thread stopped.")

    # --- MODIFIED: audio_receive_thread ---
    def audio_receive_thread(self):
        """[THREAD] Receives UDP data, routes to video or DECODES audio."""
        opus_frame_size = CHUNK # Should match sender
        expected_audio_bytes = opus_frame_size * CHANNELS * 2 # 2 bytes per int16 sample

        while self.audio_running:
            try:
                data, addr = self.udp_socket.recvfrom(65536)
                if not data: continue

                # 1. Video Packet (Same as before)
                if data.startswith(b'VID:'):
                    try:
                        parts = data.split(b':', 2)
                        if len(parts) < 3: continue
                        nickname = parts[1].decode('utf-8')
                        jpeg_data = parts[2]
                        self.safe_ui_update(self.update_video_feed, nickname, jpeg_data)
                    except Exception as e:
                        print(f"[VIDEO] Failed to decode video packet: {e} - {data[:50]}")

                # 2. Audio Packet (Now received with AUD:<nickname>:encoded_data)
                elif data.startswith(b'AUD:'):
                    parts = data.split(b':', 2)
                    if len(parts) < 3: continue
                    nickname = parts[1].decode('utf-8')
                    encoded_data = parts[2]

                    # Find or create decoder for this peer
                    if nickname not in self.peer_opus_decoders:
                        if OPUS_AVAILABLE:
                            try:
                                self.peer_opus_decoders[nickname] = opuslib.Decoder(RATE, CHANNELS)
                            except Exception as e:
                                print(f"[AUDIO] Failed to create decoder for {nickname}: {e}")
                                self.peer_opus_decoders[nickname] = None

                    decoder = self.peer_opus_decoders.get(nickname)
                    if decoder and OPUS_AVAILABLE:
                        try:
                            # Decode the audio data
                            decoded_data = decoder.decode(encoded_data, opus_frame_size)

                            # Play the decoded raw audio bytes
                            if self.speaker_stream:
                                self.speaker_stream.write(decoded_data)
                        except Exception as e:
                            # Opus decode failed, try playing as raw
                            # print(f"[AUDIO] Opus decode error from {nickname}: {e}")
                            if self.speaker_stream:
                                self.speaker_stream.write(encoded_data)
                    else:
                        # No Opus, play raw audio
                        if self.speaker_stream:
                            self.speaker_stream.write(encoded_data)

            except Exception as e:
                if self.audio_running:
                    print(f"[AV] Receive error: {e}")
                break
        print("[AV] Receive thread stopped.")

    # --- NEW: Video Functions ---
    def toggle_video(self):
        if not self.audio_running: # Need UDP to be active
            messagebox.showwarning("Audio Off", "Must be in the audio call to start video.")
            return
            
        self.is_video_on = not self.is_video_on
        
        if self.is_video_on:
            # Start the video window
            self.safe_ui_update(self.show_video_window)
            
            # Start the sending thread
            if self.video_send_thread is None or not self.video_send_thread.is_alive():
                self.video_send_thread = threading.Thread(target=self.video_send_loop, daemon=True)
                self.video_send_thread.start()
            
            self.safe_ui_update(self.video_button.config, text="Stop Video", bg="red")
        else:
            # This flag will stop the video_send_loop
            self.is_video_on = False 
            
            # Release webcam resource (will be done by the thread, but good to be safe)
            if self.video_capture:
                self.video_capture.release()
                self.video_capture = None
            
            # Remove our *own* video feed from the grid
            self.safe_ui_update(self.remove_video_feed, self.NICKNAME)
            self.safe_ui_update(self.video_button.config, text="Start Video", bg="blue")

    def video_send_loop(self):
        """[THREAD] Captures webcam and sends via UDP with VID: header."""
        try:
            self.video_capture = cv2.VideoCapture(0)
            if not self.video_capture.isOpened():
                raise Exception("Could not open webcam")
        except Exception as e:
            self.video_capture = None  # Ensure it's None on failure
            self.safe_ui_update(messagebox.showerror, "Webcam Error", f"Failed to open webcam: {e}")
            self.safe_ui_update(self.toggle_video) # Toggle back to "Off"
            return
            
        print("[VIDEO] Webcam capture started.")
        consecutive_failures = 0
        max_failures = 30  # Allow 30 consecutive failures before giving up (2 seconds at 15 FPS)
        
        while self.is_video_on: # Loop controlled by the flag
            try:
                ret, frame = self.video_capture.read()
                if not ret:
                    consecutive_failures += 1
                    if consecutive_failures >= max_failures:
                        print("[VIDEO] Too many consecutive frame grab failures. Stopping video.")
                        self.safe_ui_update(messagebox.showerror, "Webcam Error", 
                                          "Failed to read from webcam. Video stopped.")
                        self.is_video_on = False
                        break
                    time.sleep(0.1)
                    continue
                
                # Reset failure counter on success
                consecutive_failures = 0
                
                # 1. Resize (CRITICAL for LAN performance)
                frame_small = cv2.resize(frame, (320, 240))
                
                # 2. Compress to JPEG
                ret, buffer = cv2.imencode('.jpg', frame_small, [cv2.IMWRITE_JPEG_QUALITY, 50])
                if not ret:
                    continue
                
                # 3. Send over UDP with header
                self.udp_socket.sendto(b'VID:' + buffer.tobytes(), self.server_udp_addr)
                
                # 4. Display our *own* feed locally
                self.safe_ui_update(self.update_video_feed, self.NICKNAME, buffer.tobytes())
                
                time.sleep(1/15) # Aim for 15 FPS

            except Exception as e:
                if self.is_video_on:
                    print(f"[VIDEO] Send loop error: {e}")
        
        # Safely release the capture
        if self.video_capture:
            self.video_capture.release()
        self.video_capture = None
        
        # Clean up UI - ensure button state is reset
        self.safe_ui_update(self.remove_video_feed, self.NICKNAME)
        self.safe_ui_update(self.video_button.config, text="Start Video", bg="blue")
        print("[VIDEO] Webcam capture stopped.")
        
    def show_video_window(self):
        """Creates or shows the pop-up grid window for video feeds."""
        if self.video_window and self.video_window.winfo_exists():
            self.video_window.deiconify() # Un-hide if minimized
            return
            
        self.video_window = tk.Toplevel(self.window)
        self.video_window.title("Video Conference")
        self.video_window.geometry("660x500") # (320*2 + 20)
        
        self.video_window.protocol("WM_DELETE_WINDOW", self.hide_video_window)
        
        # Add existing feeds back
        for nickname in self.video_feeds.keys():
            self.rebuild_video_feed_ui(nickname)

    def hide_video_window(self):
        """Hides the video window instead of destroying it."""
        if self.video_window:
            self.video_window.withdraw() # Hide
    
    def report_user(self, reported_nickname):
        """Sends a report command to the server."""
        if not self.connected:
            messagebox.showerror("Error", "Not connected.")
            return

        if messagebox.askyesno("Report User", f"Are you sure you want to report {reported_nickname}?"):
            try:
                # Send command without lock (short message)
                self.client_socket.send(f"CMD:REPORT_USER:{reported_nickname}\n".encode('utf-8'))
                self.safe_ui_update(self.display_message, f"[SYSTEM] Your report for {reported_nickname} has been logged by the server.\n")
            except Exception as e:
                self.safe_ui_update(self.display_message, f"[SYSTEM] Failed to send report: {e}\n")
            
    def rebuild_video_feed_ui(self, nickname):
        """Helper to create the UI for a single video feed, including report button."""
        if not self.video_window or not self.video_window.winfo_exists():
            return

        # Main frame for this user's feed
        user_frame = tk.Frame(self.video_window, relief="sunken", borderwidth=1, width=320, height=260) # Slightly taller for bar
        
        # Video label (takes most space)
        label = tk.Label(user_frame, text=f"{nickname} (No Signal)", bg="black", fg="white")
        label.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # --- NEW: Bottom bar with name and report button ---
        bottom_bar = tk.Frame(user_frame, bg="#333")
        bottom_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        name_label = tk.Label(bottom_bar, text=nickname, fg="white", bg="#333")
        name_label.pack(side=tk.LEFT, padx=4, pady=2)
        
        # Don't show report button for our own feed
        if nickname != self.NICKNAME:
            report_button = tk.Button(bottom_bar, text="Report",
                                    command=lambda n=nickname: self.report_user(n),
                                    relief=tk.FLAT, bg="#333", fg="red",
                                    activebackground="#555", activeforeground="#ff6666", 
                                    borderwidth=0, font=("Helvetica", 8, "bold"),
                                    cursor="hand2")
            report_button.pack(side=tk.RIGHT, padx=4, pady=1)
        # --- End ---

        # Pack the main user frame
        user_frame.pack(side=tk.LEFT, padx=5, pady=5)
        user_frame.pack_propagate(False) # Prevent frame from shrinking to fit label text
        
        self.video_feeds[nickname] = label # Store the video label itself

    def update_video_feed(self, nickname, jpeg_data):
        """Decodes and displays a video frame in the grid."""
        if self.video_window is None or not self.video_window.winfo_exists(): 
            return # Window is hidden or closed
        
        # 1. Find or create the label for this user
        if nickname not in self.video_feeds:
            self.rebuild_video_feed_ui(nickname)
        
        # 2. Decode JPEG data
        try:
            # Handle empty data (for placeholder)
            if not jpeg_data:
                return

            data = np.frombuffer(jpeg_data, dtype=np.uint8)
            frame_bgr = cv2.imdecode(data, cv2.IMREAD_COLOR)
            frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
            
            # 3. Convert to Tkinter format
            img = Image.fromarray(frame_rgb)
            photo = ImageTk.PhotoImage(img)
            
            # 4. Update the label
            label = self.video_feeds[nickname]
            label.config(image=photo, text="") # Remove "loading" text
            label.image = photo # Keep reference
            
        except Exception as e:
            # This can happen if a packet is corrupted
            # print(f"[VIDEO] Failed to update feed for {nickname}: {e}")
            pass
            
    def remove_video_feed(self, nickname):
        """Removes a user's video feed AND audio decoder."""
        # --- NEW: Remove audio decoder ---
        if nickname in self.peer_opus_decoders:
            del self.peer_opus_decoders[nickname]
        # --- End ---
        if nickname in self.video_feeds:
            label = self.video_feeds.pop(nickname)
            if label.winfo_exists():
                # Find the parent frame and destroy it
                parent_frame = label.master
                parent_frame.destroy()

    # --- (helper functions for buffered receiving - identical to Step 4) ---
    def receive_data_inline(self, total_size, data_buffer):
        received_data = data_buffer[:total_size]
        data_buffer = data_buffer[total_size:]
        bytes_received = len(received_data)
        while bytes_received < total_size:
            remaining = total_size - bytes_received
            chunk_size = min(4096, remaining)
            try:
                chunk = self.client_socket.recv(chunk_size)
                if not chunk: raise Exception("Server disconnected")
                if len(chunk) > remaining:
                    received_data += chunk[:remaining]
                    data_buffer = chunk[remaining:] + data_buffer
                    bytes_received += remaining
                else:
                    received_data += chunk
                    bytes_received += len(chunk)
            except Exception as e:
                self.safe_ui_update(self.display_message, f"[ERROR] Receive data failed: {e}\n")
                return data_buffer, None
        return data_buffer, received_data
        
    def skip_data(self, total_size, data_buffer):
        bytes_to_skip = total_size
        skipped_from_buffer = len(data_buffer[:bytes_to_skip])
        data_buffer = data_buffer[skipped_from_buffer:]
        bytes_to_skip -= skipped_from_buffer
        while bytes_to_skip > 0:
            chunk_size = min(4096, bytes_to_skip)
            try:
                chunk = self.client_socket.recv(chunk_size)
                if not chunk: raise Exception("Server disconnected")
                bytes_to_skip -= len(chunk)
            except Exception as e:
                print(f"[ERROR] Failed to skip data: {e}")
                return b""
        return data_buffer
        
    def download_file_inline_buffered_v2(self, save_path, filesize, data_buffer):
        try:
            filename = os.path.basename(save_path)
            self.safe_ui_update(self.status_label.config, text=f"Downloading: {filename}", fg="blue")
            self.safe_ui_update(self.progress_bar.config, value=0)
            
            with open(save_path, 'wb') as f:
                bytes_received = len(data_buffer[:filesize])
                f.write(data_buffer[:filesize])
                data_buffer = data_buffer[filesize:]
                
                while bytes_received < filesize:
                    remaining = filesize - bytes_received
                    chunk_size = min(4096, remaining)
                    chunk = self.client_socket.recv(chunk_size)
                    if not chunk: raise Exception("Server disconnected")
                    
                    if len(chunk) > remaining:
                        f.write(chunk[:remaining])
                        data_buffer = chunk[remaining:] + data_buffer
                        bytes_received += remaining
                    else:
                        f.write(chunk)
                        bytes_received += len(chunk)
                    
                    progress = (bytes_received / filesize) * 100
                    self.safe_ui_update(self.progress_bar.config, value=progress)

            self.safe_ui_update(self.status_label.config, text="Download complete!", fg="green")
            self.safe_ui_update(self.display_message, f"[SYSTEM] ✓ Download complete: {save_path}\n")
        except Exception as e:
            self.safe_ui_update(self.status_label.config, text="Download failed!", fg="red")
            self.safe_ui_update(self.display_message, f"[SYSTEM] ✗ Download failed: {e}\n")
        finally:
            self.downloading = False
            self.safe_ui_update(self.download_button.config, state=tk.NORMAL)
            self.window.after(3000, lambda: self.status_label.config(text="Ready", fg="green"))
            self.window.after(3000, lambda: self.progress_bar.config(value=0))
        
        return data_buffer

    # --- MODIFIED: Main Receive Handler Thread ---
    def receive_handler(self):
        """
        [THREAD] Handles *all* incoming TCP messages and commands.
        """
        if hasattr(self, 'welcome_message'):
            self.safe_ui_update(self.display_message, self.welcome_message + "\n")
        
        data_buffer = b""

        while self.connected:
            try:
                new_data = self.client_socket.recv(4096)
                if not new_data: break
                
                data_buffer += new_data
                
                while True:
                    try:
                        newline_index = data_buffer.index(b'\n')
                        header_bytes = data_buffer[:newline_index]
                        message = header_bytes.decode('utf-8').strip()
                        data_buffer = data_buffer[newline_index + 1:]
                    except ValueError:
                        break # No complete message
                    except UnicodeDecodeError:
                        print(f"UnicodeDecodeError. Discarding buffer part.")
                        if b'\n' in data_buffer:
                            data_buffer = data_buffer[data_buffer.index(b'\n') + 1:]
                        else: data_buffer = b""
                        continue
                    
                    print(f"DEBUG: Recv '{message}'")

                    # --- Command Parsing ---
                    
                    if message.startswith('CMD:FILE_READY_TO_RECV:'):
                        filename = message.split(':', 2)[2]
                        if self.pending_upload and self.pending_upload[1] == filename:
                            threading.Thread(target=self.upload_file_thread, 
                                             args=(self.pending_upload[0], self.pending_upload[1]), 
                                             daemon=True).start()
                    
                    elif message.startswith('CMD:FILE_NEW_AVAILABLE:'):
                        parts = message.split(':', 4)
                        if len(parts) >= 5:
                            sender, filename, filesize_str = parts[2], parts[3], parts[4]
                            try:
                                filesize = int(filesize_str)
                                # Format filesize nicely
                                if filesize < 1024:
                                    size_str = f"{filesize} B"
                                elif filesize < 1024*1024:
                                    size_str = f"{filesize/1024:.1f} KB"
                                else:
                                    size_str = f"{filesize/(1024*1024):.1f} MB"

                                # Use filename as the item ID (iid) to prevent duplicates
                                iid = filename
                                
                                # This function needs to be run on the main thread
                                def update_tree():
                                    if self.file_tree.exists(iid):
                                        self.file_tree.item(iid, values=(filename, size_str, sender))
                                    else:
                                        self.file_tree.insert('', tk.END, iid=iid, values=(filename, size_str, sender))

                                self.safe_ui_update(update_tree)
                                self.available_files[filename] = (filesize, sender)
                            except (ValueError, IndexError) as e:
                                print(f"Error parsing FILE_NEW_AVAILABLE: {e}")
                    
                    elif message.startswith('CMD:FILE_SEND_START:'):
                        parts = message.split(':', 3)
                        if len(parts) >= 4:
                            filename, filesize = parts[2], int(parts[3])
                            save_path_container = [None]; dialog_done = threading.Event()
                            def ask_save_location():
                                save_path_container[0] = filedialog.asksaveasfilename(initialfile=filename)
                                dialog_done.set()
                            self.safe_ui_update(ask_save_location)
                            
                            if dialog_done.wait(timeout=60):
                                save_path = save_path_container[0]
                                if save_path:
                                    data_buffer = self.download_file_inline_buffered_v2(save_path, filesize, data_buffer)
                                else:
                                    self.safe_ui_update(self.display_message, f"[SYSTEM] Download for {filename} cancelled.\n")
                                    self.downloading = False
                                    self.safe_ui_update(self.download_button.config, state=tk.NORMAL)
                                    data_buffer = self.skip_data(filesize, data_buffer)
                            else:
                                self.safe_ui_update(self.display_message, f"[SYSTEM] Download timeout for {filename}.\n")
                                self.downloading = False
                                self.safe_ui_update(self.download_button.config, state=tk.NORMAL)
                                data_buffer = self.skip_data(filesize, data_buffer)
                    
                    elif message.startswith('CMD:PRESENTER_SET:'):
                        nickname = message.split(':', 2)[2]
                        if nickname == self.NICKNAME:
                            self.start_sharing_thread()
                        elif nickname == "NONE":
                            self.stop_sharing_thread()
                            self.safe_ui_update(self.hide_screen_view_window)
                            self.safe_ui_update(self.status_label.config, text="Ready", fg="green")
                        else:
                            self.safe_ui_update(self.show_screen_view_window)
                            self.safe_ui_update(self.status_label.config, text=f"{nickname} is presenting", fg="blue")

                    elif message.startswith('CMD:SCREEN_DATA:'):
                        try:
                            filesize = int(message.split(':', 2)[2])
                            data_buffer, image_data = self.receive_data_inline(filesize, data_buffer)
                            if image_data:
                                self.safe_ui_update(self.update_screen_view, image_data)
                        except Exception as e:
                            print(f"[ERROR] Screen data processing failed: {e}")

                    # --- G. AUDIO PORT ---
                    elif message.startswith('CMD:AUDIO_PORT:'):
                        try:
                            port = int(message.split(':', 2)[2])
                            self.init_audio(port) # Start all audio systems
                        except Exception as e:
                            print(f"[ERROR] Failed to parse AUDIO_PORT: {e}")

                    # --- H. NEW: USER_JOINED ---
                    elif message.startswith('CMD:USER_JOINED:'):
                        nickname = message.split(':', 2)[2]
                        if nickname != self.NICKNAME:
                            self.safe_ui_update(self.display_message, f"[SYSTEM] {nickname} has joined the call.\n")
                            # Create a placeholder for their video feed
                            self.safe_ui_update(self.update_video_feed, nickname, b'')

                    # --- I. NEW: USER_LEFT ---
                    elif message.startswith('CMD:USER_LEFT:'):
                        nickname = message.split(':', 2)[2]
                        if nickname != self.NICKNAME:
                            self.safe_ui_update(self.display_message, f"[SYSTEM] {nickname} has left the call.\n")
                            self.safe_ui_update(self.remove_video_feed, nickname)
                                
                    # --- J. REGULAR CHAT MESSAGE ---
                    else:
                        if not message.startswith('CMD:'):
                            self.safe_ui_update(self.display_message, message + "\n")
                        else:
                            print(f"WARNING: Unhandled command: {message}")

            except Exception as e:
                print(f"[ERROR] Disconnected from server. {e}")
                self.connected = False
                self.audio_running = False
                self.safe_ui_update(self.display_message, f"[SYSTEM] Connection error: {e}\n")
                try: self.client_socket.close()
                except: pass
                break
    
    # --- (start is identical) ---
    def start(self):
        self.window.mainloop()


if __name__ == "__main__":
    client_app = ChatClient()
    client_app.start()