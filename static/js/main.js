/**
 * Mini Bug Tracker - Main Frontend Logic
 */

// Function to toggle modal visibility
function toggleModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.toggle('hidden');
    }
}

// Close modal on Escape key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        const modals = ['addBugModal'];
        modals.forEach(id => {
            const modal = document.getElementById(id);
            if (modal && !modal.classList.contains('hidden')) {
                modal.classList.add('hidden');
            }
        });
    }
});

// Toast notification auto-dismissal (already handled by Flask flash + UI logic in base.html, 
// but we can add a timeout for explicit fade out if needed)
document.addEventListener('DOMContentLoaded', () => {
    const alerts = document.querySelectorAll('.alert-box'); // If we added this class
    setTimeout(() => {
        alerts.forEach(alert => {
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 500);
        });
    }, 5000);
});

// Priority Color Mapper (optional helper for dynamically added rows)
const priorityColors = {
    'High': 'red',
    'Medium': 'orange',
    'Low': 'green'
};
