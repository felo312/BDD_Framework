document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('loginForm');
    const errorMessage = document.getElementById('errorMessage');
    const loginBtn = document.getElementById('loginBtn');
    const btnText = loginBtn.querySelector('.btn-text');
    const btnSpinner = document.getElementById('btnSpinner');

    // Función para manejar el estado visual del botón
    const setLoading = (isLoading) => {
        if (isLoading) {
            btnText.style.display = 'none';
            btnSpinner.style.display = 'block';
            loginBtn.disabled = true;
        } else {
            btnText.style.display = 'block';
            btnSpinner.style.display = 'none';
            loginBtn.disabled = false;
        }
    };

    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        // Ocultar mensaje de error si estaba visible
        errorMessage.style.display = 'none';
        
        const username = document.getElementById('username').value.trim();
        const password = document.getElementById('password').value.trim();

        // Sanitización básica y validación
        if (!username || !password) return;

        setLoading(true);

        try {
            // OAuth2 requiere el formato application/x-www-form-urlencoded
            const formData = new URLSearchParams();
            formData.append('username', username);
            formData.append('password', password);

            const data = await fetchAPI('/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded'
                },
                body: formData,
                isLogin: true // Flag custom para no enviar token
            });

            if (data.access_token) {
                // Seguridad de Canal (Tokenización)
                localStorage.setItem('access_token', data.access_token);
                // Redirigir al dashboard
                window.location.href = 'dashboard.html';
            }

        } catch (error) {
            // Mostrar error con animación
            errorMessage.textContent = error.message || 'Credenciales incorrectas';
            errorMessage.style.display = 'block';
            
            // Reiniciar animación si ya estaba mostrada
            errorMessage.style.animation = 'none';
            errorMessage.offsetHeight; // Trigger reflow
            errorMessage.style.animation = null;
        } finally {
            setLoading(false);
        }
    });
});
