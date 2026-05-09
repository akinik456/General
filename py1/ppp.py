import pandas as pd
import requests

def fetch_and_calculate_pricing(min_price=3.99, max_price=9.99):
    # 1. Dünya Bankası'ndan PPP (Purchasing Power Parity) verilerini çek
    # PA.NUS.PPP göstergesi yerel para biriminin uluslararası dolara oranını verir
    url = "http://api.worldbank.org/v2/country/all/indicator/PA.NUS.PPP?format=json&per_page=300&date=2024"
    response = requests.get(url).json()
    
    if len(response) < 2:
        print("Veri çekilemedi.")
        return

    # 2. Veriyi temizle ve listeye al
    raw_data = response[1]
    cleaned_list = []
    
    for item in raw_data:
        if item['value'] is not None:
            cleaned_list.append({
                "CountryCode": item['countryiso3code'],
                "CountryName": item['country']['value'],
                "PPP_Value": item['value']
            })
    
    df = pd.DataFrame(cleaned_list)

    # 3. Normalizasyon: ABD'yi baz alarak katsayı (Factor) oluştur
    # Not: ABD kodu 'USA'dır.
    try:
        usd_ppp = df[df['CountryCode'] == 'USA']['PPP_Value'].values[0]
    except IndexError:
        usd_ppp = 1.0 # Fallback
        
    # Katsayı: 1.0 (ABD) ile ~0.2 (En fakir) arasında değişecek
    # Bu katsayıyı senin istediğin aralığa oturtuyoruz
    # Factor değerini 1.0 ile sınırla (Cap)
    df['Factor'] = (df['PPP_Value'] / usd_ppp).clip(0, 1.0)
    
    # 4. Formülün Uygulanması (Min-Max Ölçekleme)
    # Fiyat = Min + (Max - Min) * (Factor)
    # Not: Bazı ülkelerde PPP 1'den büyük olabilir (Norveç vb.), o yüzden katsayıyı sınırlayabilirsin
    df['RawPrice'] = min_price + (max_price - min_price) * df['Factor'].clip(0, 1.2)

    # 5. Psikolojik Yuvarlama (.99 kuralı)
    df['FinalPrice_USD'] = df['RawPrice'].apply(lambda x: int(x) + 0.99)

    # 6. CSV olarak kaydet
    df.to_csv("playstore_global_pricing.csv", index=False)
    print(f"Başarılı! 174+ ülke için fiyatlandırma 'playstore_global_pricing.csv' dosyasına kaydedildi.")

# Çalıştır
fetch_and_calculate_pricing(3.99, 9.99)