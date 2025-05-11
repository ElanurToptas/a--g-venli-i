import socket
import subprocess
import re

# OS Tespiti (TTL ile)
def ttl_ile_os_tespit(ip):
    try:
        sonuc = subprocess.check_output(["ping", "-n", "1", ip], universal_newlines=True)
        ttl = re.search(r"TTL=(\d+)", sonuc)
        if ttl:
            ttl_degeri = int(ttl.group(1))
            if ttl_degeri >= 128:
                return f"Windows (TTL={ttl_degeri})"
            elif ttl_degeri >= 64:
                return f"Linux/Unix (TTL={ttl_degeri})"
            else:
                return f"Bilinmeyen OS (TTL={ttl_degeri})"
        return "TTL bulunamadı"
    except:
        return "Ping başarısız"

# TCP port tarama
def tcp_port_taramasi(ip, port_listesi):
    print(f"\n[TCP] {ip} TCP portları taranıyor...")
    for port in port_listesi:
        try:
            soket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            soket.settimeout(0.5)
            if soket.connect_ex((ip, port)) == 0:
                print(f"[+] TCP Port {port} AÇIK")
            soket.close()
        except:
            pass

# UDP port tarama
def udp_port_taramasi(ip, port_listesi):
    print(f"\n[UDP] {ip} UDP portları taranıyor...")
    for port in port_listesi:
        try:
            soket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            soket.settimeout(1)
            soket.sendto(b"Deneme", (ip, port))
            try:
                veri, addr = soket.recvfrom(1024)
                print(f"[+] UDP Port {port} AÇIK (cevap geldi)")
            except socket.timeout:
                print(f"[?] UDP Port {port} muhtemelen AÇIK (cevap yok)")
            except Exception as e:
                if "10054" in str(e):
                    print(f"[-] UDP Port {port} KAPALI (WinError 10054)")
                else:
                    print(f"[-] UDP Port {port} hata (recvfrom): {e}")
            soket.close()
        except Exception as e:
            print(f"[-] UDP Port {port} hata (socket/send): {e}")

# Aktif IP tarama (ping ile)
def aktif_ipleri_bul(subnet):
    aktif_ipler = []
    print(f"\n[AĞ TARAMA] {subnet}.x aralığı taranıyor...")
    for i in range(1, 255):
        ip = f"{subnet}.{i}"
        sonuc = subprocess.call(['ping', '-n', '1', '-w', '500', ip], stdout=subprocess.DEVNULL)
        if sonuc == 0:
            print(f"[+] Aktif: {ip}")
            aktif_ipler.append(ip)
    return aktif_ipler

# Ana fonksiyon
def ana_tarama(subnet):
    tcp_portlar = [135, 139, 445, 5040, 80, 443]
    udp_portlar = [53, 67, 69, 123, 161, 500]

    aktifler = aktif_ipleri_bul(subnet)
    for ip in aktifler:
        print(f"\n==== {ip} analiz ediliyor ====")
        os_tahmini = ttl_ile_os_tespit(ip)
        print(f"[i] OS Tahmini: {os_tahmini}")
        tcp_port_taramasi(ip, tcp_portlar)
        udp_port_taramasi(ip, udp_portlar)

# Kullanım
ana_tarama("172.18.156")
