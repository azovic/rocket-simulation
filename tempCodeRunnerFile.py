import math

def calculate_delta_v(isp, m_initial, m_final):
    # g0: Yerçekimi ivmesi (9.81 m/s^2)
    g0 = 9.81
    delta_v = isp * g0 * math.log(m_initial / m_final)
    return delta_v

# Örnek: SpaceX Falcon 9 benzeri bir veri girişi yapalım
# m_initial: 549,000 kg (yakıt dahil)
# m_final: 25,000 kg (yakıt bittikten sonra)
# isp: 282 saniye (deniz seviyesinde)

# Fonksiyonu tanımladın, şimdi değerleri verip çağıralım:
isp_degeri = 300       # Saniye cinsinden motor verimliliği
baslangic_agirlik = 500000  # kg (Yakıt dahil)
bitis_agirlik = 50000    # kg (Yakıt bitince)

# Hesaplamayı yap ve sonucu bir değişkene ata
sonuc = calculate_delta_v(isp_degeri, baslangic_agirlik, bitis_agirlik)

# Sonucu ekrana yazdır
print(f"Roketin toplam Delta-V kapasitesi: {sonuc} m/s")

#hacklendiğimin farkındayım bırakın da işimi yapayım bana engel olamaycaksınız kusura bakmayın 
#ben bir şey istiyorsam onu mutlak suretle alırım.
#yapay zeka kullanmadan siz bile hiçbir şey yapamıyorsunuz benim yapay zekalarla konuşmama engel oluyorsunuz
#mahkemede görüşürüz
#BENİ RAHAT BIRAKIN.