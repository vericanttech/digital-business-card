// static/js/script.js
document.addEventListener('DOMContentLoaded', function() {
    // Initialize location input if it exists
    const locationInput = document.getElementById('location');
    if (locationInput) {
        initializeLocationInput(locationInput);
    }
});

function initializeLocationInput(input) {
    // Helper text element
    //const helperText = document.createElement('p');
    //helperText.className = 'mt-1 text-sm text-gray-500';
    //helperText.textContent = 'Share your location from Google Maps (e.g., https://maps.app.goo.gl/... or https://www.google.com/maps/...)';
    //input.parentNode.appendChild(helperText);

    // Update placeholder
    input.placeholder = 'Paste your Google Maps share link';

    // Optional: Add a button to get maps link
    const helpButton = document.createElement('button');
    helpButton.type = 'button';
    helpButton.className = 'mt-2 text-sm text-blue-600 hover:text-blue-800';
    helpButton.textContent = 'How to get your location link?';
    helpButton.onclick = showLocationHelp;
    input.parentNode.appendChild(helpButton);
}

function showLocationHelp() {
    alert(`To get your location link:
1. Open Google Maps
2. Search for your location
3. Click 'Share' or tap the location pin
4. Copy the provided link`);
}

// Image preview handler
function previewImage(input) {
    const preview = document.getElementById('preview-image');
    const defaultPhoto = document.getElementById('default-photo');

    if (input.files && input.files[0]) {
        const reader = new FileReader();

        reader.onload = function(e) {
            preview.src = e.target.result;
            preview.classList.remove('hidden');
            defaultPhoto.classList.add('hidden');
        }

        reader.readAsDataURL(input.files[0]);
    }
}

// QR Modal functions
function showQRModal(qrCode, cardUrl) {
    const modal = document.getElementById('qr-modal');
    if (modal) {
        document.getElementById('qr-image').src = 'data:image/png;base64,' + qrCode;
        document.getElementById('share-link').value = cardUrl;
        modal.classList.remove('hidden');
    }
}

function closeModal() {
    const modal = document.getElementById('qr-modal');
    if (modal) {
        modal.classList.add('hidden');
    }
}

function copyLink() {
    const linkInput = document.getElementById('share-link');
    if (linkInput) {
        linkInput.select();
        document.execCommand('copy');

        const button = event.target;
        const originalText = button.textContent;
        button.textContent = 'Copied!';
        setTimeout(() => {
            button.textContent = originalText;
        }, 2000);
    }
}

function shareCard(platform) {
    const url = document.getElementById('share-link').value;
    const text = "Check out my digital business card!";

    switch(platform) {
        case 'whatsapp':
            window.open(`https://wa.me/?text=${encodeURIComponent(text + ' ' + url)}`);
            break;
        case 'email':
            window.open(`mailto:?subject=Digital Business Card&body=${encodeURIComponent(text + '\n\n' + url)}`);
            break;
        case 'twitter':
            window.open(`https://twitter.com/intent/tweet?text=${encodeURIComponent(text + ' ' + url)}`);
            break;
    }
}