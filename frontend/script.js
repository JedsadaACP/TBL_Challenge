// Initialize Leaflet map
const map = L.map('map').setView([13.7563, 100.5018], 6); // Centered on Thailand

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
}).addTo(map);

// Fetch vehicle data and add markers
fetch('/api/vehicles')
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(vehicles => {
        vehicles.forEach(vehicle => {
            if (vehicle.gps_coordinates && typeof vehicle.gps_coordinates.latitude === 'number' && typeof vehicle.gps_coordinates.longitude === 'number') {
                const marker = L.marker([vehicle.gps_coordinates.latitude, vehicle.gps_coordinates.longitude]).addTo(map);
                marker.bindPopup(`<b>Registration:</b> ${vehicle.registration_number}<br><b>Unit:</b> ${vehicle.business_unit}<br><b>Status:</b> ${vehicle.status}<br><b>ETA:</b> ${vehicle.eta_hours !== null ? vehicle.eta_hours + ' hours' : 'N/A'}`);
            } else {
                console.warn("Vehicle with missing or invalid GPS coordinates:", vehicle);
            }
        });
    })
    .catch(error => {
        console.error('Error fetching vehicle data:', error);
        // Optionally, display an error message to the user on the page
        const mapDiv = document.getElementById('map');
        if (mapDiv) {
            mapDiv.innerHTML = `<p style="color: red; text-align: center;">Error loading vehicle data. Please ensure the backend is running and accessible.</p>`;
        }
    });

// --- Warehouse POV Section ---

// Get DOM Elements
const warehouseSelect = document.getElementById('warehouse-select');
const incomingShipmentsList = document.getElementById('incoming-shipments-list');

// Populate Warehouse Dropdown Function
async function populateWarehouseDropdown() {
    try {
        const response = await fetch('/api/warehouses');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const warehouses = await response.json();
        warehouses.forEach(warehouse => {
            const option = document.createElement('option');
            option.value = warehouse.warehouse_id;
            option.textContent = warehouse.name;
            warehouseSelect.appendChild(option);
        });
    } catch (error) {
        console.error('Error fetching warehouses:', error);
        warehouseSelect.innerHTML = '<option value="">Error loading warehouses</option>';
    }
}

// Display Incoming Shipments Function
async function displayIncomingShipments(warehouseId) {
    incomingShipmentsList.innerHTML = '<p>Loading shipments...</p>'; // Show loading message
    if (!warehouseId) {
        incomingShipmentsList.innerHTML = '<p>Please select a warehouse.</p>';
        return;
    }
    try {
        const response = await fetch(`/api/warehouses/${warehouseId}/incoming_shipments`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const shipments = await response.json();
        incomingShipmentsList.innerHTML = ''; // Clear loading/previous message

        if (shipments.length === 0) {
            incomingShipmentsList.innerHTML = '<p>No incoming shipments for this warehouse.</p>';
            return;
        }

        const ul = document.createElement('ul');
        shipments.forEach(shipment => {
            const li = document.createElement('li');
            let skuDetailsHtml = '<ul>';
            if (shipment.sku_details && shipment.sku_details.length > 0) {
                shipment.sku_details.forEach(sku => {
                    skuDetailsHtml += `<li>${sku.description} (Quantity: ${sku.quantity})</li>`;
                });
            } else {
                skuDetailsHtml += '<li>No SKU details available</li>';
            }
            skuDetailsHtml += '</ul>';

            li.innerHTML = `
                <b>Vehicle:</b> ${shipment.registration_number} <br>
                <b>ETA:</b> ${shipment.eta_hours !== null ? shipment.eta_hours.toFixed(2) + ' hours' : 'N/A'} <br>
                <b>Scheduled Arrival:</b> ${shipment.scheduled_arrival_time || 'N/A'} <br>
                <b>SKUs:</b> ${skuDetailsHtml}
            `;
            ul.appendChild(li);
        });
        incomingShipmentsList.appendChild(ul);
    } catch (error) {
        console.error('Error fetching incoming shipments:', error);
        incomingShipmentsList.innerHTML = '<p>Error loading shipments. Please try again.</p>';
    }
}

// Add Event Listener to Dropdown
warehouseSelect.addEventListener('change', (event) => {
    const selectedWarehouseId = event.target.value;
    displayIncomingShipments(selectedWarehouseId);
});

// Call populateWarehouseDropdown when the script loads
// Assuming the script tag is at the end of the body, direct call is fine.
populateWarehouseDropdown();
