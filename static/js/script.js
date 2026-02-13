// --- TAB SWITCHING ---
function switchTab(toolId) {
    // Hide all views
    document.querySelectorAll('.tool-view').forEach(el => el.classList.add('hidden'));
    document.getElementById('view-' + toolId).classList.remove('hidden');

    // Update buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('tab-active', 'bg-rekan-pink', 'text-white');
        btn.classList.add('bg-white', 'text-gray-800');
    });
    
    // Activate selected button
    const activeBtn = document.getElementById('tab-' + toolId);
    activeBtn.classList.remove('bg-white', 'text-gray-800');
    activeBtn.classList.add('tab-active');
}

// --- FILE NAME PREVIEWS ---
document.getElementById('heicInput').onchange = function() { 
    if(this.files[0]) document.getElementById('heicName').innerText = this.files[0].name; 
};
document.getElementById('pdfInput').onchange = function() { 
    if(this.files.length) document.getElementById('pdfName').innerText = this.files.length + " files selected"; 
};
document.getElementById('compressInput').onchange = function() { 
    if(this.files[0]) document.getElementById('compressName').innerText = this.files[0].name; 
};

// --- MAIN PROCESSOR ---
async function processTool(type) {
    let formData = new FormData();
    let endpoint = "";

    // 1. Prepare Data
    if (type === 'heic') {
        const f = document.getElementById('heicInput').files[0];
        if(!f) return alert("Please select a file first!");
        formData.append('file', f);
        endpoint = '/api/heic';
    } 
    else if (type === 'qr') {
        const txt = document.getElementById('qrInput').value;
        const logo = document.getElementById('qrLogoInput').files[0];
        if(!txt) return alert("Please enter a URL!");
        
        formData.append('text', txt);
        if(logo) formData.append('logo', logo);
        endpoint = '/api/qr';
    }
    else if (type === 'pdf') {
        const files = document.getElementById('pdfInput').files;
        if(files.length < 2) return alert("Select at least 2 PDFs to merge!");
        for (let i = 0; i < files.length; i++) {
            formData.append('files', files[i]);
        }
        endpoint = '/api/merge';
    }
    else if (type === 'compress') {
        const f = document.getElementById('compressInput').files[0];
        if(!f) return alert("Please select an image!");
        formData.append('file', f);
        endpoint = '/api/compress';
    }

    // 2. Start Game & API Call
    startGame();
    
    try {
        let response = await fetch(endpoint, { method: "POST", body: formData });
        
        if (response.ok) {
            let blob = await response.blob();
            let url = window.URL.createObjectURL(blob);
            
            // Create automatic download
            let a = document.createElement('a');
            a.href = url;
            // Name doesn't matter much, browser detects extension
            a.download = "rekan_result"; 
            document.body.appendChild(a);
            a.click();
            a.remove();
            
            // Wait 1 sec before closing game so they see the result
            setTimeout(() => {
                stopGame();
                alert("Success! Your file is downloading.");
            }, 1000);
        } else {
            stopGame();
            alert("Error processing request. Please try again.");
        }
    } catch (e) {
        console.error(e);
        stopGame();
        alert("System connection error.");
    }
}

// --- GAME LOGIC (Catch the Coin) ---
let gameInterval;
let score = 0;
const gameOverlay = document.getElementById('gameOverlay');
const gameArea = document.getElementById('gameArea');
const scoreBoard = document.getElementById('scoreBoard');

function startGame() {
    gameOverlay.classList.remove('hidden');
    score = 0;
    scoreBoard.innerText = "Score: 0";
    
    // Spawn a coin every 600ms
    gameInterval = setInterval(() => {
        spawnCoin();
    }, 600);
}

function stopGame() {
    clearInterval(gameInterval);
    gameOverlay.classList.add('hidden');
    // Clear coins
    gameArea.innerHTML = '<div id="scoreBoard" class="absolute top-2 left-4 font-bold text-xl z-10">Score: 0</div>'; 
}

function spawnCoin() {
    const coin = document.createElement('div');
    coin.innerText = "💰";
    coin.style.fontSize = "30px";
    coin.style.position = "absolute";
    coin.style.cursor = "pointer";
    coin.classList.add('coin');
    
    // Random position (Board is 300x300)
    const x = Math.random() * (250); 
    const y = Math.random() * (250);
    
    coin.style.left = x + "px";
    coin.style.top = y + "px";
    
    // Click event
    coin.onclick = function() {
        score++;
        scoreBoard.innerText = "Score: " + score;
        this.remove(); 
    };
    
    gameArea.appendChild(coin);
    
    // Coin disappears after 1.5s if missed
    setTimeout(() => {
        if(coin.parentNode) coin.remove();
    }, 1500);
}

document.getElementById('cancelProcess').onclick = stopGame;