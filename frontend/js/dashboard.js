document.addEventListener('DOMContentLoaded', () => {
    // Verificación rápida de token
    const token = localStorage.getItem('access_token');
    if (!token) {
        window.location.href = 'index.html';
        return;
    }

    let currentUser = {};
    let roles = [];
    try {
        currentUser = JSON.parse(atob(token.split('.')[1]));
        document.getElementById('userNameDisplay').textContent = currentUser.sub;
        roles = currentUser.roles || [];
        document.querySelector('.user-role').textContent = roles.length > 0 ? roles.join(', ') : 'Sin Rol';
    } catch (e) {
        document.getElementById('userNameDisplay').textContent = "Usuario";
    }

    const isAdmin = roles.includes('Administrador');
    const isMaitre = roles.includes('Maitre');
    const isMesero = roles.includes('Mesero');
    const isCocinero = roles.includes('Cocinero');

    // Ocultar opciones de menú según el rol
    if (!isAdmin) document.getElementById('nav-reportes').style.display = 'none';
    if (!isAdmin) document.getElementById('nav-empleados').style.display = 'none';
    if (!isMesero) document.getElementById('nav-pedidos').style.display = 'none';
    if (!isAdmin && !isMaitre && !isMesero) document.getElementById('nav-mesas').style.display = 'none';

    // ==========================================
    // NAVEGACIÓN SPA
    // ==========================================
    const navBtns = document.querySelectorAll('.nav-btn');
    const sections = document.querySelectorAll('.view-section');

    navBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            // Actualizar botones
            navBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            // Actualizar vistas
            const targetId = btn.getAttribute('data-target');
            sections.forEach(sec => sec.classList.remove('active'));
            document.getElementById(targetId).classList.add('active');

            // Cargar datos según la vista
            loadDataForView(targetId);
        });
    });

    document.getElementById('logoutBtn').addEventListener('click', () => {
        localStorage.removeItem('access_token');
        window.location.href = 'index.html';
    });

    // ==========================================
    // CONTROL DE VISTAS (API FETCH)
    // ==========================================
    async function loadDataForView(viewId) {
        try {
            if (viewId === 'view-reportes') await loadReportes();
            if (viewId === 'view-mesas') await loadMesas();
            if (viewId === 'view-pedidos') await loadPedidosView();
            if (viewId === 'view-empleados') await loadEmpleados();
        } catch (error) {
            console.error(`Error loading ${viewId}:`, error);
            if(error.message.includes("Operación no permitida") || error.message.includes("403")) {
                alert("No tienes permisos suficientes (Rol) para ver esta sección.");
            }
        }
    }

    // Formato de moneda COP
    const formatCOP = (valor) => {
        return new Intl.NumberFormat('es-CO', {
            style: 'currency',
            currency: 'COP',
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        }).format(valor);
    };

    // 1. REPORTES
    async function loadReportes() {
        const data = await fetchAPI('/reportes/dashboard');
        document.getElementById('stat-ingresos').textContent = formatCOP(data.ingresos_totales);
        document.getElementById('stat-pedidos').textContent = data.total_historico_pedidos;

        // Cargar detalles de pedidos para el Admin
        try {
            const detallados = await fetchAPI('/reportes/pedidos/detallados');
            const tbody = document.getElementById('detalladosTableBody');
            if (tbody) {
                tbody.innerHTML = '';
                detallados.forEach(p => {
                    const itemsStr = p.items.map(i => `${i.cantidad}x ${i.plato}`).join(', ');
                    const tr = document.createElement('tr');
                    tr.innerHTML = `
                        <td>#${p.id}</td>
                        <td>${new Date(p.fecha).toLocaleString()}</td>
                        <td>Mesa ${p.mesa_id}</td>
                        <td style="font-size:13px; color:var(--text-muted)">${itemsStr}</td>
                        <td style="font-weight:700; color:var(--accent)">${formatCOP(p.total)}</td>
                    `;
                    tbody.appendChild(tr);
                });
            }
        } catch (e) { console.error("Error cargando detalles:", e); }

        // Renderizar gráfica (si existe el contenedor)
        const chartArea = document.getElementById('chart-area');
        if (chartArea) {
            chartArea.innerHTML = '';
            if (data.frecuencia_consumo && data.frecuencia_consumo.length > 0) {
                const maxPedidos = Math.max(...data.frecuencia_consumo.map(d => d.pedidos));
                data.frecuencia_consumo.forEach(item => {
                    const height = (item.pedidos / maxPedidos) * 100;
                    const bar = document.createElement('div');
                    bar.className = 'bar';
                    bar.style.height = `${height}%`;
                    bar.innerHTML = `<span>${item.fecha.split('-').slice(1).join('/')} (${item.pedidos})</span>`;
                    chartArea.appendChild(bar);
                });
            } else {
                chartArea.innerHTML = '<p style="color:var(--text-muted)">No hay datos suficientes</p>';
            }
        }
    }

    // 2. MESAS
    async function loadMesas() {
        const mesas = await fetchAPI('/mesas/');
        const grid = document.getElementById('mesasGrid');
        grid.innerHTML = '';
        
        mesas.forEach(mesa => {
            const card = document.createElement('div');
            card.className = `mesa-card ${mesa.estado.toLowerCase()}`;
            card.innerHTML = `
                <div class="mesa-icon"><i class="ph ph-table"></i></div>
                <h3>Mesa ${mesa.id}</h3>
                <p style="color:var(--text-muted); font-size:14px; margin-bottom:10px;">Capacidad: ${mesa.sillas} pers.</p>
                <div style="font-weight:600; text-transform:uppercase; font-size:12px;">${mesa.estado}</div>
            `;
            
            if (isMaitre || isMesero || isAdmin) {
                card.style.cursor = 'pointer';
                card.addEventListener('click', async () => {
                    const isAdminOrMaitre = isAdmin || isMaitre;
                    
                    let bodyHtml = `
                        <label>Estado de la mesa:</label>
                        <select id="modal-mesa-estado" class="glass-input">
                            <option value="Disponible" ${mesa.estado === 'Disponible' ? 'selected' : ''}>Disponible</option>
                            <option value="Reservada" ${mesa.estado === 'Reservada' ? 'selected' : ''}>Reservada</option>
                            <option value="Ocupada" ${mesa.estado === 'Ocupada' ? 'selected' : ''}>Ocupada</option>
                        </select>
                    `;

                    if (isAdminOrMaitre) {
                        bodyHtml += `
                            <label>Cantidad de Sillas:</label>
                            <input type="number" id="modal-mesa-sillas" class="glass-input" value="${mesa.sillas}" min="1">
                        `;
                    }

                    window.openModal(`Gestionar Mesa ${mesa.id}`, bodyHtml, async () => {
                        const nuevoEstado = document.getElementById('modal-mesa-estado').value;
                        
                        try {
                            if (isAdminOrMaitre) {
                                const nuevasSillas = document.getElementById('modal-mesa-sillas').value;
                                await fetchAPI(`/mesas/${mesa.id}`, { 
                                    method: 'PUT',
                                    headers: { 'Content-Type': 'application/json' },
                                    body: JSON.stringify({ sillas: parseInt(nuevasSillas), estado: nuevoEstado })
                                });
                            } else {
                                await fetchAPI(`/mesas/${mesa.id}/estado?estado=${nuevoEstado}`, { method: 'PATCH' });
                            }
                            window.closeModal();
                            loadMesas();
                        } catch (e) {
                            alert(e.message);
                        }
                    });
                });
            }

            grid.appendChild(card);
        });
    }

    // 3. PEDIDOS
    let ordenActual = [];
    async function loadPedidosView() {
        const mesas = await fetchAPI('/mesas/');
        const selectMesa = document.getElementById('select-mesa');
        selectMesa.innerHTML = '<option value="">Seleccione una mesa...</option>';
        mesas.forEach(m => {
            selectMesa.innerHTML += `<option value="${m.id}">Mesa ${m.id} (${m.estado})</option>`;
        });

        const platos = await fetchAPI('/platos/');
        const selectPlato = document.getElementById('select-plato');
        selectPlato.innerHTML = '';
        platos.forEach(p => {
            selectPlato.innerHTML += `<option value="${p.id}" data-precio="${p.precio}" data-nombre="${p.nombre}">${p.nombre} (${formatCOP(p.precio)})</option>`;
        });
    }

    document.getElementById('btnAddPlato').addEventListener('click', () => {
        const select = document.getElementById('select-plato');
        const selected = select.options[select.selectedIndex];
        
        ordenActual.push({
            plato_id: parseInt(selected.value),
            nombre: selected.getAttribute('data-nombre'),
            cantidad: 1
        });
        
        renderOrden();
    });

    function renderOrden() {
        const preview = document.getElementById('ordenPreview');
        preview.innerHTML = '';
        ordenActual.forEach((item, index) => {
            preview.innerHTML += `
                <div class="orden-item">
                    <span>${item.cantidad}x ${item.nombre}</span>
                    <button type="button" onclick="window.removeOrdenItem(${index})" style="background:transparent; color:var(--danger); border:none; cursor:pointer;"><i class="ph ph-trash"></i></button>
                </div>
            `;
        });
    }

    window.removeOrdenItem = (index) => {
        ordenActual.splice(index, 1);
        renderOrden();
    };

    document.getElementById('formNuevoPedido').addEventListener('submit', async (e) => {
        e.preventDefault();
        const mesa_id = document.getElementById('select-mesa').value;
        if (!mesa_id) return alert('Selecciona una mesa');
        if (ordenActual.length === 0) return alert('Añade al menos un plato a la orden');

        try {
            const payload = {
                cliente_id: 1,
                mesero_id: 1,
                mesa_id: parseInt(mesa_id),
                ordenes: ordenActual.map(o => ({ plato_id: o.plato_id, cantidad: o.cantidad }))
            };
            
            const res = await fetchAPI('/pedidos/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            
            alert(`✅ ${res.mensaje} (Total: ${formatCOP(res.total)})`);
            ordenActual = [];
            renderOrden();
            document.getElementById('formNuevoPedido').reset();
            loadMesas();
        } catch (error) {
            alert(error.message);
        }
    });

    // 4. EMPLEADOS (CRUD)
    async function loadEmpleados() {
        const empleados = await fetchAPI('/empleados/');
        const tbody = document.getElementById('empleadosTableBody');
        tbody.innerHTML = '';
        
        empleados.forEach(emp => {
            const editBtn = `<button class="action-btn" style="color:var(--primary); background:rgba(59,130,246,0.2)" onclick="window.editarEmpleado(${emp.id}, '${emp.nombre}')"><i class="ph ph-pencil"></i> Editar</button>`;
            const deleteBtn = `<button class="action-btn" onclick="window.eliminarEmpleado(${emp.id})"><i class="ph ph-trash"></i> Eliminar</button>`;

            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>#${emp.id}</td>
                <td style="font-weight:500;">${emp.nombre}</td>
                <td><span style="background:var(--primary); padding:2px 8px; border-radius:10px; font-size:12px;">${emp.roles.join(', ') || 'Sin Rol'}</span></td>
                <td style="display:flex; gap:10px;">
                    ${editBtn}
                    ${deleteBtn}
                </td>
            `;
            tbody.appendChild(tr);
        });
    }

    // ==========================================
    // SISTEMA DE MODALES (Sustituye a prompt)
    // ==========================================
    window.openModal = (title, bodyHtml, onSaveCallback) => {
        document.getElementById('modalTitle').textContent = title;
        document.getElementById('modalBody').innerHTML = bodyHtml;
        document.getElementById('appModal').classList.add('active');
        
        const saveBtn = document.getElementById('modalSaveBtn');
        saveBtn.onclick = onSaveCallback; // Reasignar evento
    };

    window.closeModal = () => {
        document.getElementById('appModal').classList.remove('active');
    };

    // Funciones globales (CRUD Empleados UI) con Modal
    window.crearEmpleado = async () => {
        window.openModal('Crear Nuevo Empleado', `
            <input type="text" id="emp-nombre" class="glass-input" placeholder="Nombre completo" required>
            <input type="password" id="emp-clave" class="glass-input" placeholder="Contraseña" required>
            <select id="emp-rol" class="glass-input">
                <option value="1">Administrador</option>
                <option value="2">Maitre</option>
                <option value="3">Mesero</option>
                <option value="4">Cocinero</option>
            </select>
        `, async () => {
            const nombre = document.getElementById('emp-nombre').value;
            const clave = document.getElementById('emp-clave').value;
            const rol = document.getElementById('emp-rol').value;

            if(!nombre || !clave || !rol) return alert("Completa todos los campos");

            try {
                await fetchAPI('/usuarios/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ nombre: nombre, clave: clave, rol_id: parseInt(rol) })
                });
                window.closeModal();
                loadEmpleados();
            } catch (e) {
                alert(e.message);
            }
        });
    };

    window.editarEmpleado = async (id, currentName) => {
        window.openModal('Editar Empleado', `
            <input type="text" id="emp-nombre-edit" class="glass-input" value="${currentName}" required>
            <input type="password" id="emp-clave-edit" class="glass-input" placeholder="Nueva clave (dejar vacío si no cambia)">
            <select id="emp-rol-edit" class="glass-input">
                <option value="1">Administrador</option>
                <option value="2">Maitre</option>
                <option value="3">Mesero</option>
                <option value="4">Cocinero</option>
            </select>
        `, async () => {
            const nombre = document.getElementById('emp-nombre-edit').value;
            const clave = document.getElementById('emp-clave-edit').value;
            const rol = document.getElementById('emp-rol-edit').value;

            if(!nombre) return alert("El nombre es requerido");

            try {
                await fetchAPI(`/empleados/${id}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ nombre: nombre, clave: clave || "dummy", rol_id: parseInt(rol) })
                });
                window.closeModal();
                loadEmpleados();
            } catch (e) {
                alert(e.message);
            }
        });
    };

    window.eliminarEmpleado = async (id) => {
        if(confirm('¿Seguro que deseas eliminar este empleado?')) {
            try {
                await fetchAPI(`/empleados/${id}`, { method: 'DELETE' });
                loadEmpleados();
            } catch (e) {
                alert(e.message);
            }
        }
    };

    // Iniciar con la vista por defecto según el rol
    let defaultView = 'view-reportes';
    if (!isAdmin) {
        if (isMesero) defaultView = 'view-pedidos';
        else if (isMaitre) defaultView = 'view-mesas';
        else defaultView = ''; // Cocinero puede no tener vistas principales aquí
    }

    if (defaultView) {
        document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
        const defaultBtn = document.querySelector(`[data-target="${defaultView}"]`);
        if (defaultBtn) defaultBtn.classList.add('active');
        
        document.querySelectorAll('.view-section').forEach(sec => sec.classList.remove('active'));
        document.getElementById(defaultView).classList.add('active');
        
        loadDataForView(defaultView);
    }
});
