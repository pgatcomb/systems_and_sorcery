// Tabletop Campaign Finance Manager - JavaScript

// Store asset and event data for editing
let currentAssets = [];
let currentEvents = [];

// Initialize when page loads
document.addEventListener('DOMContentLoaded', function() {
    fetchAssets();
    fetchEvents();
    setupFormHandlers();
});

// ===== UTILITY FUNCTIONS =====

function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast show ${type}`;
    
    setTimeout(() => {
        toast.className = 'toast';
    }, 3000);
}

function refreshPage() {
    location.reload();
}

// ===== FETCH DATA =====

async function fetchAssets() {
    try {
        const response = await fetch('/api/assets');
        const data = await response.json();
        currentAssets = data.assets;
    } catch (error) {
        console.error('Error fetching assets:', error);
    }
}

async function fetchEvents() {
    try {
        const response = await fetch('/api/events');
        const data = await response.json();
        currentEvents = data.events;
    } catch (error) {
        console.error('Error fetching events:', error);
    }
}

// ===== TIME ADVANCEMENT =====

async function advanceTime(unit) {
    try {
        const response = await fetch('/api/advance_time', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ unit: unit })
        });
        
        const data = await response.json();
        
        if (data.success) {
            let message = `Time advanced to ${data.changes.new_date}`;
            
            // Check if we paused at an event
            if (data.changes.paused_at_event) {
                message = `⚠️ Time paused at ${data.changes.new_date} - Event(s) pending!`;
                showToast(message, 'warning');
                showPendingEventsModal(data.changes.events_pending);
            } else {
                if (data.changes.recurring_applied.length > 0) {
                    message += ` - ${data.changes.recurring_applied.length} recurring items applied`;
                }
                showToast(message, 'success');
                setTimeout(refreshPage, 1500);
            }
            
            // Update UI
            updateSummary(data.summary);
            document.getElementById('currentDate').textContent = data.changes.new_date;
            
            // Refresh graphs
            refreshGraphs();
        }
    } catch (error) {
        showToast('Failed to advance time', 'error');
        console.error('Error:', error);
    }
}

function updateSummary(summary) {
    if (summary.cash_on_hand !== undefined) {
        document.getElementById('cashOnHand').textContent = `${summary.cash_on_hand.toFixed(2)} 🪙`;
    }
    document.getElementById('netWorth').textContent = `${summary.net_worth.toFixed(2)} 🪙`;
    document.getElementById('monthlyIncome').textContent = `+${summary.monthly_income.toFixed(2)}`;
    document.getElementById('monthlyExpenses').textContent = `-${summary.monthly_expenses.toFixed(2)}`;
    
    const netElement = document.getElementById('monthlyNet');
    netElement.textContent = summary.monthly_net.toFixed(2);
    netElement.className = `summary-value ${summary.monthly_net >= 0 ? 'positive' : 'negative'}`;
}

function refreshGraphs() {
    document.getElementById('networthGraph').innerHTML = 
        '<iframe src="/api/graph/networth" frameborder="0" style="width: 100%; height: 400px;"></iframe>';
    document.getElementById('incomeExpenseGraph').innerHTML = 
        '<iframe src="/api/graph/income_expense" frameborder="0" style="width: 100%; height: 400px;"></iframe>';
}

// ===== ASSET MODAL =====

function showAssetModal() {
    document.getElementById('assetModalTitle').textContent = 'Add Asset';
    document.getElementById('assetForm').reset();
    document.getElementById('assetId').value = '';
    document.getElementById('assetModal').classList.add('active');
}

function editAsset(assetId) {
    const asset = currentAssets.find(a => a.id === assetId);
    if (!asset) return;
    
    document.getElementById('assetModalTitle').textContent = 'Edit Asset';
    document.getElementById('assetId').value = asset.id;
    document.getElementById('assetName').value = asset.name;
    document.getElementById('assetValue').value = asset.value;
    document.getElementById('assetIncome').value = asset.income;
    document.getElementById('assetExpense').value = asset.expense;
    document.getElementById('assetFrequency').value = asset.frequency;
    document.getElementById('assetModal').classList.add('active');
}

function closeAssetModal() {
    document.getElementById('assetModal').classList.remove('active');
}

async function deleteAsset(assetId) {
    if (!confirm('Are you sure you want to delete this asset?')) return;
    
    try {
        const response = await fetch(`/api/assets/${assetId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast('Asset deleted successfully', 'success');
            setTimeout(refreshPage, 1000);
        } else {
            showToast('Failed to delete asset', 'error');
        }
    } catch (error) {
        showToast('Failed to delete asset', 'error');
        console.error('Error:', error);
    }
}

// ===== EVENT MODAL =====

function showEventModal() {
    document.getElementById('eventModalTitle').textContent = 'Add Event';
    document.getElementById('eventForm').reset();
    document.getElementById('eventId').value = '';
    document.getElementById('eventModal').classList.add('active');
}

function editEvent(eventId) {
    const event = currentEvents.find(e => e.id === eventId);
    if (!event) return;
    
    document.getElementById('eventModalTitle').textContent = 'Edit Event';
    document.getElementById('eventId').value = event.id;
    document.getElementById('eventName').value = event.name;
    document.getElementById('eventAmount').value = event.amount;
    document.getElementById('eventFrequency').value = event.frequency;
    document.getElementById('eventNextDate').value = event.next_date || '';
    document.getElementById('eventDiceFormula').value = event.dice_formula || '';
    document.getElementById('eventModal').classList.add('active');
}

function closeEventModal() {
    document.getElementById('eventModal').classList.remove('active');
}

async function deleteEvent(eventId) {
    if (!confirm('Are you sure you want to delete this event?')) return;
    
    try {
        const response = await fetch(`/api/events/${eventId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast('Event deleted successfully', 'success');
            setTimeout(refreshPage, 1000);
        } else {
            showToast('Failed to delete event', 'error');
        }
    } catch (error) {
        showToast('Failed to delete event', 'error');
        console.error('Error:', error);
    }
}

// ===== CASH ON HAND MODAL =====

function showCashModal() {
    document.getElementById('cashModal').classList.add('active');
}

function closeCashModal() {
    document.getElementById('cashModal').classList.remove('active');
}

// ===== SET DATE MODAL =====

function showSetDateModal() {
    document.getElementById('setDateModal').classList.add('active');
}

function closeSetDateModal() {
    document.getElementById('setDateModal').classList.remove('active');
}

// ===== PENDING EVENTS MODAL =====

function showPendingEventsModal(events) {
    const listDiv = document.getElementById('pendingEventsList');
    listDiv.innerHTML = '';
    
    events.forEach(event => {
        const eventDiv = document.createElement('div');
        eventDiv.className = 'pending-event';
        eventDiv.style.cssText = 'padding: 15px; margin: 10px 0; border: 2px solid #f0ad4e; border-radius: 8px; background: #fcf8e3;';
        
        const amountClass = event.amount >= 0 ? 'positive' : 'negative';
        const diceInfo = event.dice_formula ? ` (Dice: ${event.dice_formula})` : '';
        
        eventDiv.innerHTML = `
            <h4 style="margin: 0 0 10px 0;">${event.name}</h4>
            <p style="margin: 5px 0;"><strong>Amount:</strong> <span class="${amountClass}">${event.amount.toFixed(2)}</span>${diceInfo}</p>
            <p style="margin: 5px 0;"><strong>Frequency:</strong> ${event.frequency}</p>
            <button class="btn btn-primary" onclick="processEvent('${event.id}')" style="margin-top: 10px;">
                ✅ Process This Event
            </button>
        `;
        
        listDiv.appendChild(eventDiv);
    });
    
    document.getElementById('pendingEventsModal').classList.add('active');
}

function closePendingEventsModal() {
    document.getElementById('pendingEventsModal').classList.remove('active');
}

async function processEvent(eventId) {
    try {
        const response = await fetch(`/api/events/${eventId}/process`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            const amount = data.event.amount;
            const amountText = amount >= 0 ? `+${amount.toFixed(2)}` : amount.toFixed(2);
            showToast(`Event "${data.event.name}" processed: ${amountText} to cash on hand`, 'success');
            
            // Update cash on hand display
            if (data.summary && data.summary.cash_on_hand !== undefined) {
                document.getElementById('cashOnHand').textContent = `${data.summary.cash_on_hand.toFixed(2)} 🪙`;
            }
            
            closePendingEventsModal();
            setTimeout(refreshPage, 1500);
        } else {
            showToast('Failed to process event', 'error');
        }
    } catch (error) {
        showToast('Failed to process event', 'error');
        console.error('Error:', error);
    }
}

// ===== EXPORT/IMPORT MODAL =====

function showExportImport() {
    document.getElementById('exportImportModal').classList.add('active');
}

function closeExportImportModal() {
    document.getElementById('exportImportModal').classList.remove('active');
}

// ===== FORM HANDLERS =====

function setupFormHandlers() {
    // Asset Form
    document.getElementById('assetForm').addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const assetId = document.getElementById('assetId').value;
        const assetData = {
            name: document.getElementById('assetName').value,
            value: parseFloat(document.getElementById('assetValue').value),
            income: parseFloat(document.getElementById('assetIncome').value),
            expense: parseFloat(document.getElementById('assetExpense').value),
            frequency: document.getElementById('assetFrequency').value
        };
        
        try {
            let url = '/api/assets';
            let method = 'POST';
            
            if (assetId) {
                url = `/api/assets/${assetId}`;
                method = 'PUT';
            }
            
            const response = await fetch(url, {
                method: method,
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(assetData)
            });
            
            const data = await response.json();
            
            if (data.success) {
                showToast(assetId ? 'Asset updated successfully' : 'Asset added successfully', 'success');
                closeAssetModal();
                setTimeout(refreshPage, 1000);
            } else {
                showToast('Failed to save asset', 'error');
            }
        } catch (error) {
            showToast('Failed to save asset', 'error');
            console.error('Error:', error);
        }
    });
    
    // Event Form
    document.getElementById('eventForm').addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const eventId = document.getElementById('eventId').value;
        const eventData = {
            name: document.getElementById('eventName').value,
            amount: parseFloat(document.getElementById('eventAmount').value),
            frequency: document.getElementById('eventFrequency').value,
            next_date: document.getElementById('eventNextDate').value || null,
            dice_formula: document.getElementById('eventDiceFormula').value || null
        };
        
        try {
            let url = '/api/events';
            let method = 'POST';
            
            if (eventId) {
                url = `/api/events/${eventId}`;
                method = 'PUT';
            }
            
            const response = await fetch(url, {
                method: method,
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(eventData)
            });
            
            const data = await response.json();
            
            if (data.success) {
                showToast(eventId ? 'Event updated successfully' : 'Event added successfully', 'success');
                closeEventModal();
                setTimeout(refreshPage, 1000);
            } else {
                showToast('Failed to save event', 'error');
            }
        } catch (error) {
            showToast('Failed to save event', 'error');
            console.error('Error:', error);
        }
    });
    
    // Cash Form
    document.getElementById('cashForm').addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const amount = parseFloat(document.getElementById('cashAmount').value);
        
        try {
            const response = await fetch('/api/cash_on_hand', {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ amount: amount })
            });
            
            const data = await response.json();
            
            if (data.success) {
                showToast('Cash on hand updated successfully', 'success');
                closeCashModal();
                updateSummary(data.summary);
                refreshGraphs();
            } else {
                showToast('Failed to update cash on hand', 'error');
            }
        } catch (error) {
            showToast('Failed to update cash on hand', 'error');
            console.error('Error:', error);
        }
    });
    
    // Set Date Form
    document.getElementById('setDateForm').addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const newDate = document.getElementById('newDate').value;
        
        try {
            const response = await fetch('/api/set_date', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ date: newDate })
            });
            
            const data = await response.json();
            
            if (data.success) {
                showToast('Date updated successfully', 'success');
                closeSetDateModal();
                document.getElementById('currentDate').textContent = data.date;
                updateSummary(data.summary);
            } else {
                showToast('Failed to update date', 'error');
            }
        } catch (error) {
            showToast('Failed to update date', 'error');
            console.error('Error:', error);
        }
    });
    
    // Import Form
    document.getElementById('importForm').addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const fileInput = document.getElementById('importFile');
        const file = fileInput.files[0];
        
        if (!file) {
            showToast('Please select a file', 'error');
            return;
        }
        
        const formData = new FormData();
        formData.append('file', file);
        
        try {
            const response = await fetch('/api/import', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (data.success) {
                showToast('Data imported successfully', 'success');
                closeExportImportModal();
                setTimeout(refreshPage, 1000);
            } else {
                showToast(`Import failed: ${data.error}`, 'error');
            }
        } catch (error) {
            showToast('Failed to import data', 'error');
            console.error('Error:', error);
        }
    });
}

// Close modals when clicking outside
window.addEventListener('click', function(event) {
    if (event.target.classList.contains('modal')) {
        event.target.classList.remove('active');
    }
});
