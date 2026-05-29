import streamlit as st
import pandas as pd
import numpy as np
from scipy.spatial import Voronoi
from shapely.geometry import Polygon, Point
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

# Кольори для брендів
BRAND_COLORS = {
    "Книгарня 'Є'": "#2CA02C",
    "Книжковий Лев": "#FF7F0E",
    "Видавництво Старого Лева": "#1F77B4",
    "Гіпотетична книгарня": "#D62728"
}

# --- ЛОГІЧНІ ФУНКЦІЇ ---

def load_data():
    """Завантаження базового словника з тестовими даними книгарень у Львові."""
    data = [
        {"name": "Є на Свободи", "brand": "Книгарня 'Є'", "lon": 24.0270, "lat": 49.8415},
        {"name": "Лев на площі", "brand": "Книжковий Лев", "lon": 24.0320, "lat": 49.8400},
        {"name": "ВСЛ Галицька", "brand": "Видавництво Старого Лева", "lon": 24.0305, "lat": 49.8395},
        {"name": "Є на Франка", "brand": "Книгарня 'Є'", "lon": 24.0335, "lat": 49.8360}
    ]
    return pd.DataFrame(data)

def calculate_voronoi(df):
    """
    Розрахунок полігонів Вороного з додаванням 4 фіктивних точок
    для замикання нескінченних променів та обрізанням по BBox Львова.
    """
    if df.empty:
        return []

    points = df[['lon', 'lat']].values
    
    # Створення BBox полігона
    bbox_polygon = Polygon([
        (LVIV_BBOX["min_lon"], LVIV_BBOX["min_lat"]),
        (LVIV_BBOX["max_lon"], LVIV_BBOX["min_lat"]),
        (LVIV_BBOX["max_lon"], LVIV_BBOX["max_lat"]),
        (LVIV_BBOX["min_lon"], LVIV_BBOX["max_lat"])
    ])

    # 4 фіктивні опорні точки (far_points) за межами міста
    far_points = np.array([
        [LVIV_BBOX["min_lon"] - 1, LVIV_BBOX["min_lat"] - 1],
        [LVIV_BBOX["max_lon"] + 1, LVIV_BBOX["min_lat"] - 1],
        [LVIV_BBOX["max_lon"] + 1, LVIV_BBOX["max_lat"] + 1],
        [LVIV_BBOX["min_lon"] - 1, LVIV_BBOX["max_lat"] + 1]
    ])

    # Об'єднуємо реальні та фіктивні точки
    all_points = np.vstack([points, far_points])
    
    # Будуємо діаграму Вороного
    vor = Voronoi(all_points)
    
    polygons = []
    # Ітеруємося тільки по реальних точках (відкидаємо останні 4)
    for i in range(len(points)):
        region_idx = vor.point_region[i]
        region_vertices_indices = vor.regions[region_idx]
        
        # Перевірка, чи регіон замкнутий (хоча з far_points вони мають бути замкнуті)
        if -1 in region_vertices_indices or len(region_vertices_indices) == 0:
            polygons.append(None)
            continue
            
        region_vertices = vor.vertices[region_vertices_indices]
        poly = Polygon(region_vertices)
        
        # Обрізаємо полігон рамкою міста (intersection)
        clipped_poly = poly.intersection(bbox_polygon)
        polygons.append(clipped_poly)
        
    return polygons

def calculate_metrics(df, polygons):
    """
    Розрахунок ключових метрик: середня площа, максимальний радіус, глобальний індекс.
    """
    total_points = len(df)
    
    areas = []
    max_radii = []
    
    # Приблизний коефіцієнт конвертації квадратних градусів у кв. км для широти Львова
    # 1 град широти ~ 111 км, 1 град довготи на 49.8 град ~ 71 км
    deg2_to_km2 = 111 * 71 
    
    for idx, row in df.iterrows():
        poly = polygons[idx]
        if poly and not poly.is_empty:
            # S_i: Площа
            areas.append(poly.area * deg2_to_km2)
            
            # R_max: Найбільша відстань від вузла до вершин полігона (в км)
            node_point = np.array([row['lon'], row['lat']])
            vertices = np.array(poly.exterior.coords)
            distances = np.linalg.norm(vertices - node_point, axis=1) * 111 # грубе наближення в км
            max_radii.append(np.max(distances))
            
    avg_area = np.mean(areas) if areas else 0.0
    max_radius = np.max(max_radii) if max_radii else 0.0
    
    # Заглушка для W (Глобальний індекс ефективності)
    # Формула: W = (Total / R_max) + (10 / S_i_avg)
    global_efficiency = (total_points / max_radius + 10 / avg_area) if max_radius > 0 and avg_area > 0 else 0.0
    
    return total_points, avg_area, max_radius, global_efficiency

def render_map(df, polygons):
    """Генерація інтерактивної карти folium."""
    # Центр Львова
    m = folium.Map(location=[49.8400, 24.0300], zoom_start=13, tiles="CartoDB positron")
    
    for idx, row in df.iterrows():
        poly = polygons[idx]
        brand = row['brand']
        color = BRAND_COLORS.get(brand, "#333333")
        
        # Додаємо маркер книгарні
        folium.CircleMarker(
            location=[row['lat'], row['lon']],
            radius=5,
            color="white",
            weight=1,
            fill=True,
            fill_color=color,
            fill_opacity=1.0,
            tooltip=f"{row['name']} ({brand})"
        ).add_to(m)
        
        # Рендеримо полігон Вороного
        if poly and not poly.is_empty and poly.geom_type in ['Polygon', 'MultiPolygon']:
            # Shapely використовує формат (lon, lat), Folium потребує (lat, lon)
            if poly.geom_type == 'Polygon':
                locations = [(lat, lon) for lon, lat in poly.exterior.coords]
                folium.Polygon(
                    locations=locations,
                    color=color,
                    weight=2,
                    fill=True,
                    fill_opacity=0.3,
                    tooltip=f"Зона обслуговування: {row['name']}"
                ).add_to(m)
                
    return m

# --- ГОЛОВНА ЛОГІКА СТОРІНКИ (STREAMLIT) ---

st.set_page_config(page_title="DSS: Зони обслуговування книгарень", layout="wide")
st.title("🗺️ DSS: Моделювання зон обслуговування книгарень у місті Львів")

# Ініціалізація стану для гіпотетичних точок
if 'hypothetical_stores' not in st.session_state:
    st.session_state.hypothetical_stores = []

# --- БОКОВА ПАНЕЛЬ (SIDEBAR) ---
with st.sidebar:
    st.header("⚙️ Керування моделлю")
    
    # 1. Завантаження базових даних та фільтрація
    base_df = load_data()
    all_brands = base_df['brand'].unique().tolist()
    
    st.subheader("Фільтр існуючих мереж")
    selected_brands = []
    for brand in all_brands:
        if st.checkbox(brand, value=True):
            selected_brands.append(brand)
            
    # 2. Форма для гіпотетичної книгарні
    st.subheader("📍 Додати гіпотетичну книгарню")
    with st.form("add_hypothetical_form"):
        # Координати центру Львова за замовчуванням
        new_lon = st.number_input("Довгота (Longitude)", value=24.0250, format="%.4f")
        new_lat = st.number_input("Широта (Latitude)", value=49.8350, format="%.4f")
        
        submit_button = st.form_submit_button(label="Симюлювати")
        
        if submit_button:
            st.session_state.hypothetical_stores.append({
                "name": f"Нова точка {len(st.session_state.hypothetical_stores) + 1}",
                "brand": "Гіпотетична книгарня",
                "lon": new_lon,
                "lat": new_lat
            })
            st.success("Точку успішно додано! Модель перераховано.")
            
    if st.button("Очистити гіпотетичні точки"):
        st.session_state.hypothetical_stores = []
        st.rerun()

# --- ПІДГОТОВКА ДАНИХ ТА РОЗРАХУНКИ ---
# Фільтруємо базові точки
filtered_df = base_df[base_df['brand'].isin(selected_brands)]

# Додаємо гіпотетичні точки
if st.session_state.hypothetical_stores:
    hypo_df = pd.DataFrame(st.session_state.hypothetical_stores)
    active_df = pd.concat([filtered_df, hypo_df], ignore_index=True)
else:
    active_df = filtered_df.copy()

# Математичне моделювання простору
polygons = calculate_voronoi(active_df)

# Розрахунок метрик
total_pts, avg_area, max_radius, w_index = calculate_metrics(active_df, polygons)

# --- ПАНЕЛЬ АНАЛІТИКИ (МЕТРИКИ) ---
st.markdown("### 📊 Ключові показники просторової доступності")
col1, col2, col3, col4 = st.columns(4)

col1.metric("Кількість точок", total_pts)
col2.metric("Середня площа зони ($S_i$)", f"{avg_area:.2f} км²")
col3.metric("Макс. радіус доступності ($R_{max}$)", f"{max_radius:.2f} км")
col4.metric("Глобальний індекс ($W$)", f"{w_index:.3f}")

st.markdown("---")

# --- ГОЛОВНИЙ ЕКРАН (КАРТА) ---
st.markdown("### 🌍 Інтерактивна карта (Діаграми Вороного)")
m = render_map(active_df, polygons)

# Рендеринг карти на всю ширину
st_folium(m, width="100%", height=600)
