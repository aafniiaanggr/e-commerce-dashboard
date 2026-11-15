import streamlit as st
import pandas as pd
import plotly.express as px
import gdown
from pathlib import Path

# Pengaturan halaman
st.set_page_config(
    page_title="E-Commerce Analytics Dashboard",
    page_icon="🛍️",
    layout="wide"
)

warna = {
    "Best Customers": "#14B8A6",
    "Loyal Customers": "#3B82F6",
    "Big Spenders": "#F59E0B",
    "Other Customers": "#64748B"
}

st.markdown("""
<style>
    .block-container {
        padding-top: 1.8rem;
        padding-bottom: 2rem;
    }
    [data-testid="stMetric"] {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        padding: 18px;
        border-radius: 12px;
    }
    [data-testid="stMetricLabel"] {
        color: #64748B;
    }
    h1, h2, h3 {
        color: #172554;
    }
</style>
""", unsafe_allow_html=True)


# Membaca data
folder_dashboard = Path(__file__).resolve().parent

@st.cache_data
def baca_data():
    link = "https://drive.google.com/uc?id=14kTplUJweSBQznT7ArZC_PACW3AdocLU"
    lokasi_file = folder_dashboard / "main_data.csv"

    if not lokasi_file.exists():
        gdown.download(link, str(lokasi_file), quiet=False)

    data = pd.read_csv(lokasi_file)
    return data

df = baca_data()


# Judul dashboard
st.title("🛍️ E-Commerce Analytics Dashboard")
st.caption(
    "Sales Performance & Customer Segmentation Analysis | "
    "Brazilian E-Commerce"
)


# Filter periode penjualan
st.sidebar.title("Dashboard Filters")
st.sidebar.markdown("Sesuaikan periode analisis penjualan.")

tanggal_awal = df["order_purchase_timestamp"].min().date()
tanggal_akhir = df["order_purchase_timestamp"].max().date()

periode = st.sidebar.date_input(
    "Periode Penjualan",
    value=(tanggal_awal, tanggal_akhir),
    min_value=tanggal_awal,
    max_value=tanggal_akhir
)

if len(periode) == 2:
    awal, akhir = periode
    data_filter = df[
        (df["order_purchase_timestamp"].dt.date >= awal) &
        (df["order_purchase_timestamp"].dt.date <= akhir)
    ].copy()
else:
    data_filter = df.copy()

if data_filter.empty:
    st.warning("Tidak terdapat data pada periode yang dipilih.")
    st.stop()


# Ringkasan penjualan
st.header("Sales Overview")

total_penjualan = data_filter["price"].sum()
jumlah_pesanan = data_filter["order_id"].nunique()

if "customer_unique_id" in data_filter.columns:
    jumlah_pelanggan = data_filter["customer_unique_id"].nunique()
else:
    jumlah_pelanggan = data_filter["customer_id"].nunique()

rata_rata_pesanan = (
    total_penjualan / jumlah_pesanan if jumlah_pesanan > 0 else 0
)

kolom1, kolom2, kolom3, kolom4 = st.columns(4)

kolom1.metric("💰 Total Revenue", f"R$ {total_penjualan:,.2f}")
kolom2.metric("📦 Total Orders", f"{jumlah_pesanan:,}")
kolom3.metric("👥 Total Customers", f"{jumlah_pelanggan:,}")
kolom4.metric("🧾 Average Order Value", f"R$ {rata_rata_pesanan:,.2f}")

st.divider()


# Tren penjualan bulanan
st.subheader("Monthly Sales Performance")

penjualan_bulanan = (
    data_filter.set_index("order_purchase_timestamp")
    .resample("ME")["price"]
    .sum()
    .reset_index()
)

penjualan_bulanan.columns = ["Bulan", "Penjualan"]

grafik_penjualan = px.area(
    penjualan_bulanan,
    x="Bulan",
    y="Penjualan",
    markers=True,
    color_discrete_sequence=["#3B82F6"],
    labels={
        "Bulan": "Month",
        "Penjualan": "Revenue (R$)"
    }
)

grafik_penjualan.update_layout(
    template="plotly_white",
    height=370,
    margin=dict(l=10, r=10, t=20, b=10),
    hovermode="x unified"
)

st.plotly_chart(grafik_penjualan, use_container_width=True)


# Analisis kategori produk
st.subheader("Product Category Performance")

if "product_category_name_english" in data_filter.columns:
    kolom_kategori = "product_category_name_english"
elif "product_category_name" in data_filter.columns:
    kolom_kategori = "product_category_name"
else:
    kolom_kategori = None

kategori_teratas = None

if kolom_kategori:
    penjualan_kategori = (
        data_filter.groupby(kolom_kategori)["price"]
        .sum()
        .sort_values(ascending=False)
        .head(10)
        .dropna()
        .reset_index()
    )

    penjualan_kategori.columns = ["Kategori", "Penjualan"]

    if not penjualan_kategori.empty:
        penjualan_kategori["Kontribusi"] = (
            penjualan_kategori["Penjualan"] /
            total_penjualan * 100
            if total_penjualan > 0 else 0
        )

        kategori_teratas = penjualan_kategori.iloc[0]["Kategori"]

        grafik_kategori = px.bar(
            penjualan_kategori.sort_values("Penjualan"),
            x="Penjualan",
            y="Kategori",
            orientation="h",
            text="Kontribusi",
            color="Penjualan",
            color_continuous_scale="Blues",
            labels={
                "Penjualan": "Revenue (R$)",
                "Kategori": "Product Category",
                "Kontribusi": "Contribution (%)"
            }
        )

        grafik_kategori.update_traces(
            texttemplate="%{text:.1f}%",
            textposition="outside"
        )

        grafik_kategori.update_layout(
            template="plotly_white",
            height=430,
            showlegend=False,
            coloraxis_showscale=False,
            margin=dict(l=10, r=40, t=20, b=10)
        )

        st.plotly_chart(grafik_kategori, use_container_width=True)

        st.info(
            f"Kategori dengan penjualan tertinggi adalah "
            f"**{kategori_teratas}**."
        )
    else:
        st.warning("Data kategori produk tidak tersedia.")
else:
    st.warning("Kolom kategori produk tidak ditemukan.")

st.divider()


# Analisis segmentasi pelanggan menggunakan RFM
st.header("Customer Segmentation Analysis")
st.caption(
    "Pengelompokan pelanggan berdasarkan Recency, Frequency, "
    "dan Monetary (RFM)."
)

if "customer_unique_id" not in data_filter.columns:
    st.warning("Kolom customer_unique_id tidak ditemukan.")
    st.stop()

data_rfm = (
    data_filter.groupby("customer_unique_id")
    .agg(
        Pembelian_Terakhir=("order_purchase_timestamp", "max"),
        Frequency=("order_id", "nunique"),
        Monetary=("price", "sum")
    )
)

tanggal_analisis = (
    data_filter["order_purchase_timestamp"].max()
    + pd.Timedelta(days=1)
)

data_rfm["Recency"] = (
    tanggal_analisis - data_rfm["Pembelian_Terakhir"]
).dt.days


# Memberikan skor RFM
data_rfm["R_Score"] = pd.qcut(
    data_rfm["Recency"].rank(method="first"),
    4,
    labels=[4, 3, 2, 1]
).astype(int)

data_rfm["F_Score"] = pd.qcut(
    data_rfm["Frequency"].rank(method="first"),
    4,
    labels=[1, 2, 3, 4]
).astype(int)

data_rfm["M_Score"] = pd.qcut(
    data_rfm["Monetary"].rank(method="first"),
    4,
    labels=[1, 2, 3, 4]
).astype(int)


# Menentukan segmen pelanggan
def tentukan_segmen(baris):
    if (
        baris["R_Score"] >= 3
        and baris["F_Score"] >= 3
        and baris["M_Score"] >= 3
    ):
        return "Best Customers"
    elif baris["F_Score"] >= 3:
        return "Loyal Customers"
    elif baris["M_Score"] >= 3:
        return "Big Spenders"
    else:
        return "Other Customers"


data_rfm["Segment"] = data_rfm.apply(tentukan_segmen, axis=1)


# Ringkasan setiap segmen
ringkasan_rfm = (
    data_rfm.groupby("Segment")
    .agg(
        Customers=("Segment", "count"),
        Revenue=("Monetary", "sum"),
        Avg_Recency=("Recency", "mean"),
        Avg_Frequency=("Frequency", "mean"),
        Avg_Monetary=("Monetary", "mean")
    )
    .reset_index()
)

total_revenue_rfm = ringkasan_rfm["Revenue"].sum()

ringkasan_rfm["Revenue Contribution"] = (
    ringkasan_rfm["Revenue"] / total_revenue_rfm * 100
    if total_revenue_rfm > 0 else 0
)

segmen_teratas = ringkasan_rfm.loc[
    ringkasan_rfm["Revenue"].idxmax()
]


# Ringkasan performa RFM
st.subheader("RFM Performance Highlights")

kolom_rfm1, kolom_rfm2, kolom_rfm3 = st.columns(3)

kolom_rfm1.metric(
    "Most Valuable Segment",
    segmen_teratas["Segment"]
)

kolom_rfm2.metric(
    "Highest Revenue Contribution",
    f"{segmen_teratas['Revenue Contribution']:.1f}%"
)

kolom_rfm3.metric(
    "Customer Segments",
    f"{data_rfm['Segment'].nunique()}"
)


# Visualisasi segmentasi pelanggan
st.subheader("Customer Segment Distribution")

kolom_grafik1, kolom_grafik2 = st.columns(2)

with kolom_grafik1:
    grafik_segmentasi = px.pie(
        ringkasan_rfm,
        names="Segment",
        values="Customers",
        hole=0.58,
        color="Segment",
        color_discrete_map=warna
    )

    grafik_segmentasi.update_traces(
        textposition="inside",
        textinfo="percent+label"
    )

    grafik_segmentasi.update_layout(
        template="plotly_white",
        height=400,
        margin=dict(l=10, r=10, t=30, b=10),
        showlegend=False
    )

    st.plotly_chart(grafik_segmentasi, use_container_width=True)

with kolom_grafik2:
    grafik_revenue = px.bar(
        ringkasan_rfm.sort_values("Revenue"),
        x="Revenue",
        y="Segment",
        orientation="h",
        text="Revenue Contribution",
        color="Segment",
        color_discrete_map=warna,
        labels={
            "Revenue": "Revenue (R$)",
            "Segment": "Customer Segment",
            "Revenue Contribution": "Revenue Contribution (%)"
        }
    )

    grafik_revenue.update_traces(
        texttemplate="%{text:.1f}%",
        textposition="outside"
    )

    grafik_revenue.update_layout(
        template="plotly_white",
        height=400,
        showlegend=False,
        margin=dict(l=10, r=40, t=30, b=10)
    )

    st.plotly_chart(grafik_revenue, use_container_width=True)


# Perbandingan karakteristik RFM
st.subheader("RFM Characteristics by Segment")

pilihan_metrik = st.selectbox(
    "Pilih karakteristik pelanggan",
    ["Avg_Recency", "Avg_Frequency", "Avg_Monetary"],
    format_func=lambda x: {
        "Avg_Recency": "Average Recency (Days)",
        "Avg_Frequency": "Average Frequency (Orders)",
        "Avg_Monetary": "Average Monetary (R$)"
    }[x]
)

grafik_rfm = px.bar(
    ringkasan_rfm,
    x="Segment",
    y=pilihan_metrik,
    color="Segment",
    color_discrete_map=warna,
    text_auto=".2f"
)

grafik_rfm.update_layout(
    template="plotly_white",
    height=350,
    showlegend=False,
    margin=dict(l=10, r=10, t=20, b=10)
)

st.plotly_chart(grafik_rfm, use_container_width=True)


# Tabel ringkasan pelanggan
st.subheader("Customer Segment Details")

tabel_rfm = ringkasan_rfm.rename(columns={
    "Segment": "Customer Segment",
    "Customers": "Total Customers",
    "Revenue": "Total Revenue (R$)",
    "Avg_Recency": "Avg Recency (Days)",
    "Avg_Frequency": "Avg Frequency",
    "Avg_Monetary": "Avg Monetary (R$)",
    "Revenue Contribution": "Revenue Contribution (%)"
})

st.dataframe(
    tabel_rfm.style.format({
        "Total Customers": "{:,.0f}",
        "Total Revenue (R$)": "R$ {:,.2f}",
        "Avg Recency (Days)": "{:.1f}",
        "Avg Frequency": "{:.2f}",
        "Avg Monetary (R$)": "R$ {:,.2f}",
        "Revenue Contribution (%)": "{:.2f}%"
    }),
    use_container_width=True,
    hide_index=True
)


# Insight dan rekomendasi bisnis
st.divider()
st.header("Business Insights & Recommendations")

st.markdown(f"""
**1. Customer Value**

Segmen **{segmen_teratas['Segment']}** memiliki total revenue
terbesar dengan kontribusi sebesar
**{segmen_teratas['Revenue Contribution']:.1f}%** dari total
revenue seluruh pelanggan.

**2. Customer Retention**

Pelanggan dengan Recency rendah menunjukkan transaksi yang
lebih baru. Strategi retensi dapat diarahkan pada pelanggan
dengan Frequency dan Monetary yang tinggi.

**3. Sales Strategy**

Kategori produk dengan penjualan tertinggi dapat menjadi
prioritas dalam strategi promosi dan pengelolaan stok.
""")

st.caption(
    "Data Source: Brazilian E-Commerce Public Dataset by Olist"
)

