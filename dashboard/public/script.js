const API_BASE_URL = 'http://127.0.0.1:5001/api'; // Your Flask backend URL
let map;
let truckMarkers = {}; // To keep track of markers: truckId -> L.Marker
let allTrucksData = []; // Store all fetched truck data for filtering
let selectedTruckId = null; // To track the currently selected truck for highlighting

// Custom Icon Definitions (using external CDN for colored markers)
const icons = {
    // Outbound = Factory -> Warehouse, Inbound = Warehouse -> Factory
    sermsuk_outbound: L.icon({ iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-green.png', shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png', iconSize: [25, 41], iconAnchor: [12, 41], popupAnchor: [1, -34], shadowSize: [41, 41] }),
    sermsuk_inbound: L.icon({ iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-gold.png', shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png', iconSize: [25, 41], iconAnchor: [12, 41], popupAnchor: [1, -34], shadowSize: [41, 41] }), // Gold for Sermsuk inbound
    tbl_outbound: L.icon({ iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-blue.png', shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png', iconSize: [25, 41], iconAnchor: [12, 41], popupAnchor: [1, -34], shadowSize: [41, 41] }),
    tbl_inbound: L.icon({ iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-violet.png', shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png', iconSize: [25, 41], iconAnchor: [12, 41], popupAnchor: [1, -34], shadowSize: [41, 41] }), // Violet for TBL inbound
    delayed: L.icon({ iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png', shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png', iconSize: [25, 41], iconAnchor: [12, 41], popupAnchor: [1, -34], shadowSize: [41, 41] }),
    warehouse: L.icon({ iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-grey.png', shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png', iconSize: [25, 41], iconAnchor: [12, 41], popupAnchor: [1, -34], shadowSize: [41, 41] }),
    factory: L.icon({ iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-black.png', shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png', iconSize: [25, 41], iconAnchor: [12, 41], popupAnchor: [1, -34], shadowSize: [41, 41] })
};

document.addEventListener('DOMContentLoaded', () => {
    initializeMap();
    fetchStaticLocations();
    fetchTruckData(); // Initial fetch
    setInterval(fetchTruckData, 7000); // Refresh data every 7 seconds

    document.getElementById('truck-search').addEventListener('input', (e) => {
        filterTruckList(e.target.value);
    });
});

async function initializeMap() {
    let initialLat = 13.7563; // Bangkok default
    let initialLng = 100.5018;

    try { // Try to center on warehouse
        const response = await fetch(`${API_BASE_URL}/warehouse-location`);
        if (response.ok) {
            const loc = await response.json();
            initialLat = loc.latitude;
            initialLng = loc.longitude;
        }
    } catch (error) { console.warn('Could not fetch warehouse location for map init.', error); }

    map = L.map('map').setView([initialLat, initialLng], 12); // Zoom level 12
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);
}

async function fetchStaticLocations() {
    try {
        const [warehouseRes, factoryRes] = await Promise.all([
            fetch(`${API_BASE_URL}/warehouse-location`),
            fetch(`${API_BASE_URL}/factory-location`)
        ]);

        if (warehouseRes.ok) {
            const loc = await warehouseRes.json();
            L.marker([loc.latitude, loc.longitude], { icon: icons.warehouse, zIndexOffset: 500 }) // ensure on top
                .addTo(map)
                .bindPopup(`<b>${loc.name}</b><br>(${loc.latitude.toFixed(4)}, ${loc.longitude.toFixed(4)})`);
        }
        if (factoryRes.ok) {
            const loc = await factoryRes.json();
            L.marker([loc.latitude, loc.longitude], { icon: icons.factory, zIndexOffset: 500 }) // ensure on top
                .addTo(map)
                .bindPopup(`<b>${loc.name}</b><br>(${loc.latitude.toFixed(4)}, ${loc.longitude.toFixed(4)})`);
        }
    } catch (error) {
        console.error('Error fetching static locations:', error);
    }
}

async function fetchTruckData() {
    try {
        const response = await fetch(`${API_BASE_URL}/trucks`);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        
        allTrucksData = await response.json();
        filterTruckList(document.getElementById('truck-search').value); // Apply current filter
        updateMapMarkers(allTrucksData); // Update map with all trucks initially
        updateStatsBar(allTrucksData);

        // If a truck was selected, refresh its details
        if (selectedTruckId) {
            const currentlySelectedTruck = allTrucksData.find(t => t.truck_id === selectedTruckId);
            if (currentlySelectedTruck) {
                showTruckDetails(currentlySelectedTruck);
            } else { // Selected truck no longer exists or data changed
                clearTruckDetails();
                selectedTruckId = null;
            }
        }

    } catch (error) {
        console.error('Error fetching truck data:', error);
        document.getElementById('truck-list').innerHTML = '<p class="error-message">Error loading truck data. Please try again later.</p>';
    }
}

function filterTruckList(searchTerm) {
    const lowerSearchTerm = searchTerm.toLowerCase();
    const filteredTrucks = allTrucksData.filter(truck => {
        const matchesTruckId = truck.truck_id.toLowerCase().includes(lowerSearchTerm);
        const matchesSku = truck.shipments && truck.shipments.some(shipment => 
            shipment.sku.toLowerCase().includes(lowerSearchTerm)
        );
        return matchesTruckId || matchesSku;
    });
    renderTruckList(filteredTrucks);
}


function renderTruckList(trucksToRender) {
    const truckListDiv = document.getElementById('truck-list');
    truckListDiv.innerHTML = ''; 

    if (trucksToRender.length === 0) {
        truckListDiv.innerHTML = '<p>No trucks match your search or available.</p>';
        return;
    }

    trucksToRender.sort((a, b) => { // Sort: Delayed first, then by ID
        if (a.is_delayed && !b.is_delayed) return -1;
        if (!a.is_delayed && b.is_delayed) return 1;
        return a.truck_id.localeCompare(b.truck_id);
    });

    trucksToRender.forEach(truck => {
        const truckItem = document.createElement('div');
        truckItem.classList.add('truck-item');
        if (truck.truck_id === selectedTruckId) {
            truckItem.classList.add('active-selection');
        }

        // BU Tag
        const buTagClass = truck.business_unit === 'Sermsuk' ? 'bu-sermsuk' : 'bu-tbl';
        
        // Status Indicator
        let statusText = truck.status.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()); // Capitalize
        let statusClass = `status-${truck.status.toLowerCase().replace(/\s+/g, '_')}`;
        if (truck.is_delayed) {
            statusText += " (Delayed)";
            statusClass = `status-delayed ${statusClass}`; // Add delayed class, keep original for color if not red
        }

        const etaDate = truck.eta ? new Date(truck.eta).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'N/A';
        const directionArrow = truck.direction === 'outbound' ? '→' : '←';


        truckItem.innerHTML = `
            <div>
                <strong>${truck.truck_id}</strong> <span class="bu-tag ${buTagClass}">${truck.business_unit}</span>
            </div>
            <p><span class="status-indicator ${statusClass}">${statusText}</span></p>
            <p>Route: ${truck.origin} ${directionArrow} ${truck.destination}</p>
            <p>Calculated ETA: ${etaDate}</p>
        `;
        truckItem.addEventListener('click', () => {
            selectedTruckId = truck.truck_id;
            showTruckDetails(truck);
            map.setView([truck.latitude, truck.longitude], 15); // Center map on selected truck
            renderTruckList(trucksToRender); // Re-render list to update active selection
        });
        truckListDiv.appendChild(truckItem);
    });
}

function getTruckIcon(truck) {
    if (truck.is_delayed) return icons.delayed;
    if (truck.business_unit === "Sermsuk") {
        return truck.direction === "outbound" ? icons.sermsuk_outbound : icons.sermsuk_inbound;
    } else if (truck.business_unit === "TBL") {
        return truck.direction === "outbound" ? icons.tbl_outbound : icons.tbl_inbound;
    }
    // Fallback default icon (shouldn't be needed if data is clean)
    return L.icon({ iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png', iconSize: [25, 41], iconAnchor: [12, 41]});
}

function updateMapMarkers(trucks) {
    const currentTruckIdsOnMap = Object.keys(truckMarkers);
    const truckIdsInData = trucks.map(t => t.truck_id);

    // Remove markers for trucks no longer in the data
    currentTruckIdsOnMap.forEach(truckId => {
        if (!truckIdsInData.includes(truckId)) {
            if (map.hasLayer(truckMarkers[truckId])) {
                map.removeLayer(truckMarkers[truckId]);
            }
            delete truckMarkers[truckId];
        }
    });
    
    trucks.forEach(truck => {
        if (typeof truck.latitude !== 'number' || typeof truck.longitude !== 'number') {
            console.warn(`Skipping truck ${truck.truck_id} due to invalid coordinates.`);
            return;
        }
        const latLng = [truck.latitude, truck.longitude];
        const icon = getTruckIcon(truck);

        if (truckMarkers[truck.truck_id]) { // Marker exists, update it
            truckMarkers[truck.truck_id].setLatLng(latLng).setIcon(icon);
        } else { // New marker
            truckMarkers[truck.truck_id] = L.marker(latLng, { icon: icon }).addTo(map);
        }
        
        const etaTime = truck.eta ? new Date(truck.eta).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'N/A';
        let statusDisplay = truck.status.replace('_', ' ');
        if (truck.is_delayed) statusDisplay += ' <span style="color:red; font-weight:bold;">(Delayed)</span>';

        let popupContent = `
            <strong class="popup-truck-id">${truck.truck_id} (${truck.business_unit})</strong>
            Status: ${statusDisplay}<br>
            Speed: ${truck.speed_kmh || 0} km/h<br>
            Direction: ${truck.origin} → ${truck.destination}<br>
            Calc. ETA: ${etaTime}<br>
            <button class="popup-button" onclick='handlePopupDetailsClick("${truck.truck_id}")'>View Details</button>
        `;
        truckMarkers[truck.truck_id].bindPopup(popupContent);
    });
}

// Expose to global scope for popup button
window.handlePopupDetailsClick = function(truckId) {
    const truck = allTrucksData.find(t => t.truck_id === truckId);
    if (truck) {
        selectedTruckId = truck.truck_id;
        showTruckDetails(truck);
        map.setView([truck.latitude, truck.longitude], 15);
        filterTruckList(document.getElementById('truck-search').value); // Re-render list for active state
    }
}

function showTruckDetails(truck) {
    const detailsDiv = document.getElementById('truck-details');
    const etaDate = truck.eta ? new Date(truck.eta).toLocaleString() : 'N/A';
    const lastUpdatedDate = truck.last_updated ? new Date(truck.last_updated).toLocaleString() : 'N/A';

    let statusText = truck.status.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
    let statusClass = `status-${truck.status.toLowerCase().replace(/\s+/g, '_')}`;
     if (truck.is_delayed) {
        statusText += " (Delayed)";
        statusClass = `status-delayed ${statusClass}`;
    }


    let shipmentsHtml = '<h4>Shipment Details:</h4>';
    if (truck.shipments && truck.shipments.length > 0) {
        truck.shipments.forEach(shipment => {
            const expectedArrival = shipment.expected_arrival_time ? new Date(shipment.expected_arrival_time).toLocaleString() : 'N/A';
            shipmentsHtml += `
                <div class="shipment-item">
                    <p><strong>Order ID:</strong> ${shipment.order_id || 'N/A'}</p>
                    <p><strong>SKU:</strong> ${shipment.sku}</p>
                    <p><strong>Quantity:</strong> ${shipment.quantity}</p>
                    <p><strong>ASN Expected Arrival:</strong> ${expectedArrival}</p>
                </div>
            `;
        });
    } else {
        shipmentsHtml += '<p>No shipment data available for this truck.</p>';
    }

    detailsDiv.innerHTML = `
        <h3>${truck.truck_id} <span class="bu-tag bu-${truck.business_unit.toLowerCase()}">${truck.business_unit}</span></h3>
        <p><strong>Status:</strong> <span class="status-indicator ${statusClass}">${statusText}</span></p>
        <p><strong>Direction:</strong> ${truck.origin} → ${truck.destination} (${truck.direction})</p>
        <p><strong>Current Speed:</strong> ${truck.speed_kmh || 0} km/h</p>
        <p><strong>Location (Lat, Lng):</strong> ${truck.latitude.toFixed(6)}, ${truck.longitude.toFixed(6)}</p>
        <p><strong>Calculated ETA (by Control Tower):</strong> ${etaDate}</p>
        <p><strong>Last GPS Update:</strong> ${lastUpdatedDate}</p>
        <div class="shipment-info">
            ${shipmentsHtml}
        </div>
    `;
}

function clearTruckDetails() {
    const detailsDiv = document.getElementById('truck-details');
    detailsDiv.innerHTML = '<p>Click on a truck in the list or on the map to see details.</p>';
}

function updateStatsBar(trucks) {
    const totalTrucks = trucks.length;
    const enRouteTrucks = trucks.filter(t => t.status === 'en_route').length;
    const delayedTrucks = trucks.filter(t => t.is_delayed).length;

    document.getElementById('total-trucks').textContent = `Total Trucks: ${totalTrucks}`;
    document.getElementById('trucks-enroute').textContent = `En Route: ${enRouteTrucks}`;
    document.getElementById('trucks-delayed').textContent = `Delayed: ${delayedTrucks}`;
}