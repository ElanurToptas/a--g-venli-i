import socket
import subprocess
import re
import concurrent.futures
import platform

# OS Tespiti (TTL ile)
def ttl_ile_os_tespit(ip):
    try:
        param = '-n' if platform.system().lower() == 'windows' else '-c'
        sonuc = subprocess.check_output(["ping", param, "1", ip], universal_newlines=True)
        ttl = re.search(r"TTL=(\d+)", sonuc, re.IGNORECASE)
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

# Port -> Servis adı tahmini tablosu
port_servis_dict = {
    80: "HTTP",
    443: "HTTPS",
    135: "Microsoft RPC",
    139: "NetBIOS Session Service",
    445: "Microsoft-DS (SMB)",
    5040: "Windows Remote Management",
    53: "DNS",
    67: "DHCP",
    69: "TFTP",
    123: "NTP",
    161: "SNMP",
    500: "IPSec",
}

# TCP port tarama ve banner alma (paralel işçi fonksiyonu)
def tarama_ve_servis_bulma(args):
    ip, port = args
    try:
        soket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        soket.settimeout(1)
        sonuc = soket.connect_ex((ip, port))
        if sonuc == 0:
            banner = ""
            try:
                # HTTP portuysa GET isteği gönder
                if port == 80:
                    soket.sendall(b"GET / HTTP/1.0\r\n\r\n")
                elif port == 443:
                    # HTTPS banner almak için SSL gerekiyor, basit soketle olmaz, atla
                    pass
                banner = soket.recv(1024).decode(errors='ignore').strip()
            except:
                pass

            servis_ismi = port_servis_dict.get(port, "Bilinmiyor")
            if banner:
                # Banner varsa, sadece ilk satırı göster
                banner_ilk_satir = banner.splitlines()[0]
                return (port, True, f"{servis_ismi} - Banner: {banner_ilk_satir}")
            else:
                return (port, True, servis_ismi)
        soket.close()
        return (port, False, "")
    except Exception as e:
        return (port, False, f"Hata: {e}")

def tcp_port_taramasi_tum_portlar(ip):
    print(f"\n[TCP] {ip} TCP portları (1-1024) paralel taranıyor...")
    portlar = range(1, 1024)

    with concurrent.futures.ThreadPoolExecutor(max_workers=200) as executor:
        args = ((ip, port) for port in portlar)
        for port, acik_mi, servis_bilgi in executor.map(tarama_ve_servis_bulma, args):
            if acik_mi:
                print(f"[+] TCP Port {port} AÇIK - Servis: {servis_bilgi}")

# UDP port tarama (var olan fonksiyonun aynısı)
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
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    for i in range(1, 255):
        ip = f"{subnet}.{i}"
        sonuc = subprocess.call(['ping', param, '1', '-w', '500', ip], stdout=subprocess.DEVNULL)
        if sonuc == 0:
            print(f"[+] Aktif: {ip}")
            aktif_ipler.append(ip)
    return aktif_ipler

# Ana fonksiyon
def ana_tarama(subnet):
    udp_portlar = [53, 67, 69, 123, 161, 500]

    aktifler = aktif_ipleri_bul(subnet)
    for ip in aktifler:
        print(f"\n==== {ip} analiz ediliyor ====")
        os_tahmini = ttl_ile_os_tespit(ip)
        print(f"[i] OS Tahmini: {os_tahmini}")
        tcp_port_taramasi_tum_portlar(ip)
        udp_port_taramasi(ip, udp_portlar)

# Kullanım örneği
ana_tarama("192.168.43")
