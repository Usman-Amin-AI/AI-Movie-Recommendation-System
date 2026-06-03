import pickle
import streamlit as st
import requests
from typing import Tuple, List

# ---------------- Configuration ----------------
TMDB_API_KEY = "8265bd1679663a7ea12ac168da84d2e8"
TMDB_BASE_URL = "https://api.themoviedb.org/3"
POSTER_BASE_URL = "https://image.tmdb.org/t/p/w500"
PLACEHOLDER_IMAGE = "https://via.placeholder.com/500x750?text=No+Image"

# ---------------- API Functions ----------------
@st.cache_data(ttl=3600)
def fetch_poster(movie_id: int) -> str:
    """Fetch movie poster URL from TMDB API with caching."""
    try:
        url = f"{TMDB_BASE_URL}/movie/{movie_id}?api_key={TMDB_API_KEY}&language=en-US"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        poster_path = data.get('poster_path')
        return f"{POSTER_BASE_URL}{poster_path}" if poster_path else PLACEHOLDER_IMAGE
    except Exception as e:
        st.warning(f"Error fetching poster: {e}")
        return PLACEHOLDER_IMAGE

@st.cache_data(ttl=3600)
def fetch_movie_details(movie_id: int) -> Tuple[float, str, List[str], str]:
    """Fetch detailed movie information from TMDB API with caching."""
    try:
        url = f"{TMDB_BASE_URL}/movie/{movie_id}?api_key={TMDB_API_KEY}&language=en-US"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        rating = round(data.get('vote_average', 0), 1)
        year = data.get('release_date', 'N/A')[:4] if data.get('release_date') else 'N/A'
        genres = [g['name'] for g in data.get('genres', [])][:3]  # Limit to 3 genres
        overview = data.get('overview', 'No overview available.')
        
        return rating, year, genres, overview
    except Exception as e:
        st.warning(f"Error fetching movie details: {e}")
        return 0.0, 'N/A', [], 'No overview available.'

def recommend(movie: str, movies_df, similarity_matrix) -> Tuple:
    """Generate movie recommendations based on similarity scores."""
    try:
        index = movies_df[movies_df['title'] == movie].index[0]
        distances = sorted(
            list(enumerate(similarity_matrix[index])), 
            reverse=True, 
            key=lambda x: x[1]
        )

        recommendations = {
            'names': [],
            'posters': [],
            'ratings': [],
            'years': [],
            'genres': [],
            'overviews': []
        }

        for i in distances[1:6]:  # Get top 5 recommendations
            movie_id = movies_df.iloc[i[0]].movie_id
            movie_title = movies_df.iloc[i[0]].title
            
            poster = fetch_poster(movie_id)
            rating, year, genres, overview = fetch_movie_details(movie_id)
            
            recommendations['names'].append(movie_title)
            recommendations['posters'].append(poster)
            recommendations['ratings'].append(rating)
            recommendations['years'].append(year)
            recommendations['genres'].append(genres)
            recommendations['overviews'].append(overview)

        return (
            recommendations['names'],
            recommendations['posters'],
            recommendations['ratings'],
            recommendations['years'],
            recommendations['genres'],
            recommendations['overviews']
        )
    except IndexError:
        st.error("Movie not found in database!")
        return [], [], [], [], [], []

# ---------------- Streamlit Configuration ----------------
st.set_page_config(
    page_title="AI - Movie Recommender",
    layout="wide",
    page_icon="🎬",
    initial_sidebar_state="collapsed"
)

# ---------------- Custom Styling ----------------
st.markdown("""
    <style>
    /* Global Styles */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .main { background: linear-gradient(135deg, #0f0f0f 0%, #1a1a1a 100%); }
    
    /* Header Styles */
    .app-header {
        text-align: center;
        padding: 2rem 0 1rem 0;
        background: linear-gradient(90deg, #e50914 0%, #b20710 100%);
        border-radius: 16px;
        margin-bottom: 2rem;
        box-shadow: 0 10px 40px rgba(229, 9, 20, 0.3);
    }
    
    .app-title {
        font-size: 3rem;
        font-weight: 700;
        color: #ffffff;
        margin: 0;
        text-shadow: 2px 2px 8px rgba(0,0,0,0.5);
    }
    
    .app-subtitle {
        font-size: 1.1rem;
        color: #f0f0f0;
        margin-top: 0.5rem;
    }
    
    /* Movie Card Styles */
    .movie-card {
        background: linear-gradient(145deg, #1e1e1e, #2a2a2a);
        border-radius: 16px;
        padding: 1rem;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        border: 1px solid #333;
        height: 100%;
        position: relative;
        overflow: hidden;
    }
    
    .movie-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(135deg, rgba(229, 9, 20, 0.1) 0%, transparent 100%);
        opacity: 0;
        transition: opacity 0.4s ease;
        pointer-events: none;
    }
    
    .movie-card:hover {
        transform: translateY(-12px) scale(1.02);
        box-shadow: 0 20px 60px rgba(229, 9, 20, 0.4);
        border-color: #e50914;
    }
    
    .movie-card:hover::before {
        opacity: 1;
    }
    
    .poster-container {
        border-radius: 12px;
        overflow: hidden;
        position: relative;
        box-shadow: 0 8px 24px rgba(0,0,0,0.4);
        margin-bottom: 1rem;
    }
    
    .poster-container img {
        width: 100%;
        display: block;
        transition: transform 0.4s ease;
    }
    
    .movie-card:hover .poster-container img {
        transform: scale(1.05);
    }
    
    .movie-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: #ffffff;
        margin: 0.75rem 0 0.5rem 0;
        text-align: center;
        line-height: 1.3;
        min-height: 2.6rem;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    
    .movie-meta {
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 1rem;
        margin: 0.5rem 0;
        font-size: 0.95rem;
        color: #b0b0b0;
    }
    
    .rating {
        display: flex;
        align-items: center;
        gap: 0.3rem;
        color: #ffd700;
        font-weight: 600;
    }
    
    .year {
        color: #888;
    }
    
    .genre-container {
        display: flex;
        flex-wrap: wrap;
        gap: 0.4rem;
        justify-content: center;
        margin-top: 0.75rem;
    }
    
    .genre-badge {
        background: linear-gradient(135deg, #e50914, #b20710);
        color: #fff;
        padding: 0.3rem 0.75rem;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        box-shadow: 0 2px 8px rgba(229, 9, 20, 0.3);
    }
    
    .overview {
        font-size: 0.85rem;
        color: #aaa;
        line-height: 1.5;
        text-align: center;
        margin-top: 0.75rem;
        display: -webkit-box;
        -webkit-line-clamp: 3;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }
    
    /* Button Styles */
    div.stButton > button {
        background: linear-gradient(90deg, #e50914 0%, #b20710 100%);
        color: white;
        font-weight: 700;
        padding: 0.75rem 2.5rem;
        border-radius: 12px;
        border: none;
        font-size: 1.1rem;
        transition: all 0.3s ease;
        box-shadow: 0 6px 20px rgba(229, 9, 20, 0.4);
        text-transform: uppercase;
        letter-spacing: 1px;
        width: 100%;
    }
    
    div.stButton > button:hover {
        box-shadow: 0 0 30px 10px rgba(229, 9, 20, 0.6);
        transform: translateY(-2px);
    }
    
    /* Selectbox Styles */
    div.stSelectbox > div > div {
        border-radius: 12px;
        padding: 0.75rem;
        border: 2px solid #333;
        background-color: #1e1e1e;
        color: #fff;
        font-size: 1rem;
        transition: all 0.3s ease;
    }
    
    div.stSelectbox > div > div:focus-within {
        border-color: #e50914;
        box-shadow: 0 0 20px rgba(229, 9, 20, 0.3);
    }
    
    /* Loading Animation */
    .stSpinner > div {
        border-top-color: #e50914 !important;
    }
    
    /* Responsive adjustments */
    @media (max-width: 768px) {
        .app-title { font-size: 2rem; }
        .movie-title { font-size: 0.95rem; }
    }
    </style>
""", unsafe_allow_html=True)

# ---------------- Header ----------------
st.markdown("""
    <div class="app-header">
        <h1 class="app-title">🎬 AI - Movie Recommender</h1>
        <p class="app-subtitle">Discover your next favorite movie with AI-powered recommendations</p>
    </div>
""", unsafe_allow_html=True)

# ---------------- Load Data ----------------
try:
    movies = pickle.load(open('movie_list.pkl', 'rb'))
    similarity = pickle.load(open('similarity.pkl', 'rb'))
except FileNotFoundError:
    st.error("⚠️ Required data files not found. Please ensure 'movie_list.pkl' and 'similarity.pkl' are in the same directory.")
    st.stop()

# ---------------- Search Interface ----------------
col1, col2, col3 = st.columns([1, 3, 1])
with col2:
    selected_movie = st.selectbox(
        "🔍 Search for a movie:",
        options=movies['title'].values,
        help="Start typing to search for a movie or select from below"
    )
    
    if st.button('✨ Get Recommendations'):
        with st.spinner('Finding perfect matches for you...'):
            names, posters, ratings, years, genres_list, overviews = recommend(
                selected_movie, movies, similarity
            )
            
            if names:
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("### 🎯 Top 5 Recommendations")
                st.markdown("<br>", unsafe_allow_html=True)
                
                # Display in responsive columns
                cols = st.columns(5)
                for idx, (col, name, poster, rating, year, genres, overview) in enumerate(
                    zip(cols, names, posters, ratings, years, genres_list, overviews)
                ):
                    with col:
                        st.markdown(f"""
                            <div class="movie-card">
                                <div class="poster-container">
                                    <img src="{poster}" alt="{name}">
                                </div>
                                <div class="movie-title">{name}</div>
                                <div class="movie-meta">
                                    <span class="rating">⭐ {rating}</span>
                                    <span class="year">{year}</span>
                                </div>
                                <div class="genre-container">
                                    {''.join([f'<span class="genre-badge">{g}</span>' for g in genres])}
                                </div>
                                <div class="overview">{overview}</div>
                            </div>
                        """, unsafe_allow_html=True)

# ---------------- Footer ----------------
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("""
    <div style='text-align: center; color: #666; font-size: 0.9rem; padding: 2rem 0;'>
        <p>Powered by AI | Made by Usman Amin</p>
    </div>
""", unsafe_allow_html=True)