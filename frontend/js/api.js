// Archivo base para configurar las llamadas a la API (Vanilla JS)
const API_URL = 'http://127.0.0.1:8000';

/**
 * Realiza una petición genérica al backend.
 * @param {string} endpoint - La ruta de la API (ej. '/login')
 * @param {object} options - Opciones de fetch
 */
async function fetchAPI(endpoint, options = {}) {
    const token = localStorage.getItem('access_token');

    const headers = {
        ...options.headers
    };

    if (token && !options.isLogin) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    try {
        const response = await fetch(`${API_URL}${endpoint}`, {
            ...options,
            headers
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => null);
            throw new Error(errorData?.detail || 'Error en la petición');
        }

        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}
