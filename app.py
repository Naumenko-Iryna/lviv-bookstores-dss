import streamlit as st
import pandas as pd
import numpy as np
from scipy.spatial import Voronoi
from shapely.geometry import Polygon
import folium
from streamlit_folium import st_folium

# --- КОНСТАНТИ ТА НАЛАШТУВАННЯ ---
# Базова рамка Львова (Bounding Box)
LVIV_BBOX = {
    "min_lon": 23.9000,
    "min_lat": 49.7700,
    "max_lon": 24.1500,
    "max_lat": 49.9000
}

# Координати умовного центру (Площа Ринок) для демографічного градієнта
LVIV_CENTER = {"lat": 49.8410, "lon": 24.0315}

# Кольори для брендів книгарень
BRAND_COLORS = {
    "Видавництво Старого Лева": "#1F77B4",
    "Vivat": "#9467BD",
    "Книгарня Є": "#2CA02C",
    "КСД": "#D62728",
    "Перший клас": "#FF7F0E",
    "Одиночні": "#7F7F7F",
    "Гіпотетична книгарня": "#E377C2"
}

# --- ЛОГІЧНІ ФУНКЦІЇ ---

def load_data():
    """Завантаження повного масиву існуючих книгарень міста Львова."""
    data = [
        # Видавництво Старого Лева
        {"name": "ВСЛ (вул. Галицька, 17)", "brand": "Видавництво Старого Лева", "lon": 24.0305000000, "lat": 49.8395000000},
        {"name": "ВСЛ (вул. Краківська, 3)", "brand": "Видавництво Старого Лева", "lon": 24.0305880000, "lat": 49.8424740000},
        {"name": "ВСЛ (вул. Личаківська, 22)", "brand": "Видавництво Старого Лева", "lon": 24.0409500000, "lat": 49.8397160000},
        
        # Vivat
        {"name": "Vivat (Пл. Галицька, 12)", "brand": "Vivat", "lon": 24.0325000000, "lat": 49.8395000000},
        {"name": "Vivat (Просп. Шевченка, 22)", "brand": "Vivat", "lon": 24.0314000000, "lat": 49.8364000000},
        
        # Книгарня Є
        {"name": "Книгарня Є (Просп. Свободи, 7)", "brand": "Книгарня Є", "lon": 24.0255444444, "lat": 49.8443416667},
        {"name": "Книгарня Є (Вул. Костюшка, 5)", "brand": "Книгарня Є", "lon": 24.0239703101, "lat": 49.8398790384},
        {"name": "Книгарня Є (Пл. Міцкевича, 1)", "brand": "Книгарня Є", "lon": 24.0306191254, "lat": 49.8389114189},
        {"name": "Книгарня Є (Просп. Шевченка, 17)", "brand": "Книгарня Є", "lon": 24.0315453542, "lat": 49.8370997643},
        {"name": "Книгарня Є (Вул. Театральна, 10)", "brand": "Книгарня Є", "lon": 24.0298273561, "lat": 49.8415715575},
        {"name": "Книгарня Є (Вул. С. Бандери, 73)", "brand": "Книгарня Є", "lon": 24.0065601812, "lat": 49.8349153918},
        {"name": "Книгарня Є (Вул. Стрийська, 30)", "brand": "Книгарня Є", "lon": 24.0286042677, "lat": 49.8273463303},
        
        # КСД
        {"name": "КСД (вул. Личаківська, 1)", "brand": "КСД", "lon": 24.0368370524, "lat": 49.8399708417},
        {"name": "КСД (вул. Корнякта, 1)", "brand": "КСД", "lon": 24.0295159966, "lat": 49.8435302037},
        {"name": "КСД (вул. Братів Рогатинців, 15)", "brand": "КСД", "lon": 24.0322980947, "lat": 49.8404595331},
        {"name": "КСД (вул. Городоцька, 179)", "brand": "КСД", "lon": 23.9950993524, "lat": 49.8352558709},
        
        # Перший клас
        {"name": "Перший клас (вул. Личаківська, 4)", "brand": "Перший клас", "lon": 24.0378528389, "lat": 49.8395977586},
        {"name": "Перший клас (вул. Кн. Ольги, 65)", "brand": "Перший клас", "lon": 24.0003243236, "lat": 49.8100722666},
        {"name": "Перший клас (вул. Ч. Калини, 65)", "brand": "Перший клас", "lon": 24.0563289101, "lat": 49.7977394530},
        {"name": "Перший клас (вул. Петлюри, 2)", "brand": "Перший клас", "lon": 23.9776341812, "lat": 49.8235691178},
        {"name": "Перший клас (вул. Широка, 65А)", "brand": "Перший клас", "lon": 23.9700215524, "lat": 49.8418400950},
        {"name": "Перший клас (вул. Грінченка, 2)", "brand": "Перший клас", "lon": 24.0558937677, "lat": 49.8709461028},
        {"name": "Перший клас (вул. Г. Мазепи, 11)", "brand": "Перший клас", "lon": 24.0326024666, "lat": 49.8710710396},
        {"name": "Перший клас (вул. Гайдамацька, 18)", "brand": "Перший клас", "lon": 24.0283872101, "lat": 49.8536466663},
        {"name": "Перший клас (вул. В. Великого, 59В)", "brand": "Перший клас", "lon": 24.0011142677, "lat": 49.8093284267},
        {"name": "Перший клас (вул. Ак. Лазаренка, 2)", "brand": "Перший клас", "lon": 24.0195354542, "lat": 49.8147103298},
        
        # Одиночні
        {"name": "Книгарня на Федорова", "brand": "Одиночні", "lon": 24.0330261677, "lat": 49.8427454928},
        {"name": "Книгарня Артефактів", "brand": "Одиночні", "lon": 24.0385319812, "lat": 49.8400571994},
        {"name": "Книгарня ПЛЕКАЙ", "brand": "Одиночні", "lon": 24.0338575254, "lat": 49.8336574947},
        {"name": "Книгарня НТШ", "brand": "Одиночні", "lon": 24.0310081984, "lat": 49.8376515838},
        {"name": "Книжковий Лев", "brand": "Одиночні", "lon": 24.0312140812, "lat": 49.8371861669},
        {"name": "Книгарня №1", "brand": "Одиночні", "lon": 24.0325372947, "lat": 49.8425862932},
        {"name": "Книгарня 'Ноти'", "brand": "Одиночні", "lon": 24.0311104917, "lat": 49.8370624726},
        {"name": "Bookling", "brand": "Одиночні", "lon": 24.0219647677, "lat": 49.8493620205},
        {"name": "Книгарня на Привокзальній", "brand": "Одиночні", "lon": 24.0039800000, "lat": 49.8366000000},
        {"name": "Шувар", "brand": "Одиночні", "lon": 24.0468416965, "lat": 49.7983738512},
        {"name": "Кавова сторінка", "brand": "Одиночні", "lon": 23.9900101254, "lat": 49.8203447809},
        {"name": "Дім книги", "brand": "Одиночні", "lon": 24.0604868761, "lat": 49.7855874110},
        {"name": "Книгарня Книги", "brand": "Одиночні", "lon": 23.9496458000, "lat": 49.8695381795},
        {"name": "Фоліо", "brand": "Одиночні", "lon": 24.0282087831, "lat": 49.8390789406}
    ]
    return pd.DataFrame(data)

def calculate_voronoi(df):
    """Розрахунок замкнутих полігонів Вороного, обмежених контуром міста."""
    if df.empty:
        return []

    points = df[['lon', 'lat']].values
    bbox_polygon = Polygon([
        (LVIV_BBOX["min_lon"], LVIV_BBOX["min_lat"]),
        (LVIV_BBOX["max_lon"], LVIV_BBOX["min_lat"]),
        (LVIV_BBOX["max_lon"], LVIV_BBOX["max_lat"]),
        (LVIV_BBOX["min_lon"], LVIV_BBOX["max_lat"])
    ])

    # Додавання 4 фіктивних точок далеко за межами міста для стабілізації країв
    far_points = np.array([
        [LVIV_BBOX["min_lon"] - 2, LVIV_BBOX["min_lat"] - 2],
        [LVIV_BBOX["max_lon"] + 2, LVIV_BBOX["min_lat"] - 2],
        [LVIV_BBOX["max_lon"] + 2, LVIV_BBOX["max_lat"] + 2],
        [LVIV_BBOX["min_lon"] - 2, LVIV_BBOX["max_lat"] + 2]
    ])

    all_points = np.vstack([points, far_points])
    vor = Voronoi(all_points)
    
    polygons = []
    for i in range(len(points)):
        region_idx = vor.point_region[i]
        region_vertices_indices = vor.regions[region_idx]
        
        if -1 in region_vertices_indices or len(region_vertices_indices) == 0:
            polygons.append(Polygon())
            continue
            
        region_vertices = vor.vertices[region_vertices_indices]
        poly = Polygon(region_vertices)
        clipped_poly = poly.intersection(bbox_polygon)
        polygons.append(clipped_poly)
        
    return polygons

def analyze_spatial_data(df, polygons, alpha, beta, gamma):
    """Обчислення просторових, морфологічних та демографічних метрик для кожної точки."""
    analyzed_data = []
    
    # Коефіцієнти переводу градусів у кілометри для проекції Львова
    deg_lat_to_km = 111.0
    deg_lon_to_km = 71.5
    deg2_to_km2 = deg_lat_to_km * deg_lon_to_km

    for idx, row in df.iterrows():
        poly = polygons[idx]
        
        if poly and not poly.is_empty:
            # 1. Площа зони (S_i) у кв. км
            area_km2 = poly.area * deg2_to_km2
            
            # 2. Максимальний радіус доступності (R_max) у км
            node_coord = np.array([row['lon'], row['lat']])
            vertices = np.array(poly.exterior.coords)
            
            dx = (vertices[:, 0] - node_coord[0]) * deg_lon_to_km
            dy = (vertices[:, 1] - node_coord[1]) * deg_lat_to_km
            distances = np.sqrt(dx**2 + dy**2)
            max_r_km = np.max(distances) if len(distances) > 0 else 0.1
            
            # 3. Моделювання густоти населення (осіб/км²) на основі віддаленості від центру
            dist_to_center = np.sqrt(
                ((row['lon'] - LVIV_CENTER["lon"]) * deg_lon_to_km)**2 + 
                ((row['lat'] - LVIV_CENTER["lat"]) * deg_lat_to_km)**2
            )
            pop_density = max(2200, 11500 - (dist_to_center * 1400))
            
            # 4. Індекс компактності форми Полсбі-Поппера
            perimeter_coords = list(poly.exterior.coords)
            p_len = 0.0
            for i in range(len(perimeter_coords) - 1):
                p_dx = (perimeter_coords[i+1][0] - perimeter_coords[i][0]) * deg_lon_to_km
                p_dy = (perimeter_coords[i+1][1] - perimeter_coords[i][1]) * deg_lat_to_km
                p_len += np.sqrt(p_dx**2 + p_dy**2)
            
            compactness = (4 * np.pi * area_km2) / (p_len ** 2) if p_len > 0 else 0.0
        else:
            area_km2, max_r_km, pop_density, compactness = 0.0, 0.1, 2000, 0.0

        analyzed_data.append({
            "Назва книгарні": row['name'],
            "Бренд": row['brand'],
            "Площа зони ($S_i$), км²": round(area_km2, 2),
            "Радіус доступності ($R_{max}$), км": round(max_r_km, 2),
            "Густота населення, осіб/км²": int(pop_density),
            "Індекс компактності ($C_i$)": round(compactness, 3)
        })

    res_df = pd.DataFrame(analyzed_data)
    
    # Нормалізація параметрів для розрахунку W
    max_s = res_df["Площа зони ($S_i$), км²"].max() if res_df["Площа зони ($S_i$), км²"].max() > 0 else 1
    max_inv_r = (1 / res_df["Радіус доступності ($R_{max}$), км"]).max()
    max_dens = res_df["Густота населення, осіб/км²"].max()
    
    norm_s = res_df["Площа зони ($S_i$), км²"] / max_s
    norm_inv_r = (1 / res_df["Радіус доступності ($R_{max}$), км"]) / max_inv_r
    norm_dens_comp = (res_df["Густота населення, осіб/км²"] * res_df["Індекс компактності ($C_i$)"]) / (max_dens * 1)
    
    res_df["Індекс ефективності ($W_i$)"] = (alpha * norm_s) + (beta * norm_inv_r) + (gamma * norm_dens_comp)
    res_df["Індекс ефективності ($W_i$)"] = res_df["Індекс ефективності ($W_i$)"].round(3)

    return res_df

def render_map(df, polygons):
    """Генерація інтерактивного шару карти."""
    m = folium.Map(location=[49.8410, 24.0315], zoom_start=13, tiles="CartoDB positron")
    
    for idx, row in df.iterrows():
        poly = polygons[idx]
        brand = row['brand']
        color = BRAND_COLORS.get(brand, "#333333")
        
        folium.CircleMarker(
            location=[row['lat'], row['lon']],
            radius=6,
            color="black",
            weight=1,
            fill=True,
            fill_color=color,
            fill_opacity=0.9,
            tooltip=f"<b>{row['name']}</b><br>Мережа: {brand}"
        ).add_to(m)
        
        if poly and not poly.is_empty:
            locations = [(lat, lon) for lon, lat in poly.exterior.coords]
            folium.Polygon(
                locations=locations,
                color=color,
                weight=1.5,
                fill=True,
                fill_opacity=0.25,
                tooltip=f"Зона обслуговування: {row['name']}"
            ).add_to(m)
                
    return m

# --- ВЕБ-ІНТЕРФЕЙС (STREAMLIT) ---

st.set_page_config(page_title="GIS Моделювання: Книгарні Львова", layout="wide")
st.title("🗺️ Геоінформаційна система аналізу зон обслуговування книгарень м. Львова")
st.markdown("Модель просторового розподілу на основі обмежених діаграм Вороного, метрик форми та демографічного потенціалу.")

# Ініціалізація стану для симуляційного шару
if 'hypothetical_stores' not in st.session_state:
    st.session_state.hypothetical_stores = []

# --- САЙДБАР: КЕРУВАННЯ ПАРАМЕТРАМИ ---
with st.sidebar:
    st.header("⚙️ Вхідні параметри моделі")
    
    st.subheader("🎛️ Вагові коефіцієнти індексу W")
    st.caption("Регулюють пріоритетність факторів при оцінці просторової структури")
    
    alpha = st.slider("Альфа (α) — Вага площі покриття S_i", 0.0, 1.0, 0.3, 0.05)
    beta = st.slider("Бета (β) — Вага крокової доступності (1/R_max)", 0.0, 1.0, 0.4, 0.05)
    gamma = st.slider("Гамма (γ) — Вага демографії та геометрії", 0.0, 1.0, 0.3, 0.05)
    
    sum_weights = alpha + beta + gamma
    if sum_weights > 0:
        alpha_n = alpha / sum_weights
        beta_n = beta / sum_weights
        gamma_n = gamma / sum_weights
    else:
        alpha_n, beta_n, gamma_n = 0.33, 0.33, 0.33

    st.info(f"Нормалізовані ваги: α={alpha_n:.2f} | β={beta_n:.2f} | γ={gamma_n:.2f}")
    
    base_df = load_data()
    all_brands = base_df['brand'].unique().tolist()
    st.subheader("🌐 Мережі книгарень в аналізі")
    selected_brands = [b for b in all_brands if st.checkbox(b, value=True)]
            
    st.subheader("📍 Симуляція нової локації")
    with st.form("add_hypothetical_form"):
        new_lon = st.number_input("Довгота (Lon)", value=24.0150, format="%.4f")
        new_lat = st.number_input("Широта (Lat)", value=49.8300, format="%.4f")
        submit_button = st.form_submit_button(label="Провести симуляцію")
        
        if submit_button:
            st.session_state.hypothetical_stores.append({
                "name": f"Гіпотетична точка #{len(st.session_state.hypothetical_stores) + 1}",
                "brand": "Гіпотетична книгарня",
                "lon": new_lon,
                "lat": new_lat
            })
            st.toast("Об'єкт додано. Геометрію Вороного перераховано.")
            
    if st.session_state.hypothetical_stores:
        if st.button("Скинути симуляційні точки"):
            st.session_state.hypothetical_stores = []
            st.rerun()

# --- ОБРОБКА ДАНИХ ТА ГЕОМЕТРИЧНИЙ АНАЛІЗ ---
filtered_df = base_df[base_df['brand'].isin(selected_brands)]

if st.session_state.hypothetical_stores:
    hypo_df = pd.DataFrame(st.session_state.hypothetical_stores)
    active_df = pd.concat([filtered_df, hypo_df], ignore_index=True)
else:
    active_df = filtered_df.copy()

polygons = calculate_voronoi(active_df)
analysis_results_df = analyze_spatial_data(active_df, polygons, alpha_n, beta_n, gamma_n)

# --- ВИТЯГ ГЛОБАЛЬНИХ МЕТРИК ---
global_w = analysis_results_df["Індекс ефективності ($W_i$)"].mean()
avg_s = analysis_results_df["Площа зони ($S_i$), км²"].mean()
max_r = analysis_results_df["Радіус доступності ($R_{max}$), км"].max()

# --- ВІДОБРАЖЕННЯ ІНТЕРФЕЙСУ ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("Кількість локацій (N)", len(active_df))
col2.metric("Сер. площа покриття (S_avg)", f"{avg_s:.2f} км²")
col3.metric("Макс. плече доступності (R_max)", f"{max_r:.2f} км")
col4.metric("Глобальний індекс системи (W)", f"{global_w:.3f}")

st.markdown("---")

st.subheader("🌍 Інтерактивна картосхема геопросторових бар'єрів")
m = render_map(active_df, polygons)
st_folium(m, width="100%", height=550)

st.markdown("---")

st.subheader("📋 Матриця просторових характеристик об'єктів")
st.markdown("Кожен рядок представляє розраховані геометричні та геомаркетингові параметри індивідуального полігона:")

st.dataframe(
    analysis_results_df,
    column_config={
        "Густота населення, осіб/км²": st.column_config.NumberColumn(format="%d"),
        "Індекс ефективності ($W_i$)": st.column_config.ProgressColumn(
            "Індекс ефективності ($W_i$)",
            help="Інтегральний показник ефективності на основі α, β, γ",
            format="%.3f",
            min_value=0.0,
            max_value=1.0
        )
    },
    use_container_width=True,
    hide_index=True
)

with st.expander("🔬 Методологічна довідка та математичний апарат"):
    st.markdown("""
    * **Компактність форми ($C_i$):** Розраховується за методом Полсбі-Поппера. Показує відхилення форми зони обслуговування від ідеального кола (ідеальна ізотропна доступність).
    * **Демографічна щільність:** Розрахована через радіальну функцію згасання від геометричного ядра міста $D(d) = D_{max} - k \cdot d$, що моделює реальний спад щільності від центру до периферійних вузлів.
    * **Нормалізація індексу $W$:** Щоб уникнути зміщення через різницю в одиницях вимірювання (км², км, особи), перед згорткою кожен вектор ознак ділиться на його максимальне значення в поточній вибірці.
    """)
