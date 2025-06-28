import pandas as pd
import re

def preprocess_initial(df):
    # Cari baris awal yang mengandung angka (1, 1.1, dst)
    start_row = df[df[0].astype(str).str.contains(r'^\d+(\.\d+)?$', na=False)].index[0]

    # Ambil data dari baris tersebut
    data = df.iloc[start_row:].reset_index(drop=True)
    data.columns = ['No', 'Lokasi'] + [f'Hari_{i}' for i in range(1, len(data.columns) - 1)]

    # Bersihkan kolom
    data['No'] = data['No'].astype(str).str.strip()
    data['Lokasi'] = data['Lokasi'].astype(str).apply(lambda x: re.sub(r'[\u200b\xa0]+', ' ', x)).str.strip()

    # Ubah harga jadi numerik
    for col in data.columns[2:]:
        data[col] = pd.to_numeric(data[col].str.replace('.', '', regex=False), errors='coerce')

    # Tandai baris wilayah
    data['IsWilayah'] = ~data['No'].str.contains(r'\.', na=False)

    # Sebarkan nama wilayah ke bawah
    data['Wilayah'] = data['Lokasi'].where(data['IsWilayah']).ffill()

    # ============================
    # Proses Data Pasar
    # ============================
    pasar_df = data[~data['IsWilayah']].copy()
    harga_cols = [col for col in data.columns if col.startswith("Hari_")]
    pasar_df['RataRataHargaPasar'] = pasar_df[harga_cols].mean(axis=1)

    # Rekap per wilayah
    rekap_df = pasar_df.groupby('Wilayah').agg(
        JumlahPasar=('Lokasi', 'count'),
        RataRataHarga=('RataRataHargaPasar', 'mean'),
        RataRataHargaTertinggiDiPasar=('RataRataHargaPasar', 'max')
    ).reset_index()

    # Ambil nama pasar dengan harga tertinggi
    idx_max = pasar_df.groupby('Wilayah')['RataRataHargaPasar'].idxmax()
    tertinggi_df = pasar_df.loc[idx_max, ['Wilayah', 'Lokasi']].rename(
        columns={'Lokasi': 'PasarDenganRataRataHargaTertinggi'}
    )

    # Gabungkan
    final_df = rekap_df.merge(tertinggi_df, on='Wilayah')
    final_df.insert(0, 'No', range(1, len(final_df) + 1))
    final_df.rename(columns={'Wilayah': 'Lokasi'}, inplace=True)

    # ============================
    # Tambahkan Latitude & Longitude untuk Wilayah
    # ============================
    koordinat = {
        'Kota Surabaya': (-7.2575, 112.7521),
        'Kota Malang': (-7.9819, 112.6265),
        'Kota Kediri': (-7.8166, 112.0114),
        'Kabupaten Sidoarjo': (-7.4467, 112.7181),
        'Kabupaten Gresik': (-7.1607, 112.6530),
        'Kota Mojokerto': (-7.4722, 112.4336),
        'Kota Pasuruan': (-7.6451, 112.9086),
        'Kabupaten Lamongan': (-7.1120, 112.4148),
        'Kabupaten Jombang': (-7.5469, 112.2334),
        'Kabupaten Tuban': (-6.8971, 112.0505),
        'Kabupaten Bangkalan': (-7.0335, 112.7467),
        'Kabupaten Bojonegoro': (-7.1500, 111.8833),
        'Kabupaten Mojokerto': (-7.4700, 112.4330),
        'Kabupaten Pasuruan': (-7.6895, 112.6855),
        'Kabupaten Probolinggo': (-7.7764, 113.2196),
        'Kota Probolinggo': (-7.7543, 113.2150),
        'Kabupaten Banyuwangi': (-8.2186, 114.3690),
        'Kabupaten Blitar': (-8.0941, 112.3096),
        'Kabupaten Bondowoso': (-7.9135, 113.8213),
        'Kabupaten Jember': (-8.1725, 113.7005),
        'Kabupaten Lumajang': (-8.1350, 113.2249),
        'Kabupaten Madiun': (-7.6295, 111.5230),
        'Kabupaten Magetan': (-7.6524, 111.3355),
        'Kabupaten Nganjuk': (-7.6055, 111.9031),
        'Kabupaten Ngawi': (-7.4059, 111.4468),
        'Kabupaten Pamekasan': (-7.1566, 113.4780),
        'Kabupaten Ponorogo': (-7.8659, 111.4691),
        'Kabupaten Sampang': (-7.1917, 113.2490),
        'Kabupaten Sumenep': (-6.9245, 113.9066),
        'Kabupaten Situbondo': (-7.7069, 114.0099),
        'Kabupaten Trenggalek': (-8.0593, 111.7084),
        'Kabupaten Tulungagung': (-8.0657, 111.9010),
        'Kota Batu': (-7.8671, 112.5239),
        'Kota Blitar': (-8.0987, 112.1680),
        'Kota Madiun': (-7.6309, 111.5230),
        'Kabupaten Kediri': (-7.8480, 112.0113),
        'Kabupaten Malang': (-8.1065, 112.6660),
        'Kabupaten Pacitan': (-8.1948, 111.1056)
    }

    final_df['Latitude'] = final_df['Lokasi'].map(lambda x: koordinat.get(x, (None, None))[0])
    final_df['Longitude'] = final_df['Lokasi'].map(lambda x: koordinat.get(x, (None, None))[1])

    return final_df


def winsorize_series(series):
    Q1 = series.quantile(0.25)
    Q3 = series.quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    return series.clip(lower=lower_bound, upper=upper_bound)


def preprocess(df):
    target_cols = ['RataRataHarga', 'RataRataHargaTertinggiDiPasar']
    
    df_clean = df.copy()
    for col in target_cols:
        df_clean[col] = winsorize_series(df_clean[col])
    return df_clean
