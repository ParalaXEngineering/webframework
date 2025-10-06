// ============================================================================
// EASTER EGGS MODULE
// Framework easter eggs: Konami code, pixel mode, death screen, etc.
// ============================================================================

// Konami Code Animation
(function() {
    const konamiCode = ['ArrowUp', 'ArrowUp', 'ArrowDown', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'ArrowLeft', 'ArrowRight', 'b', 'a'];
    let konamiIndex = 0;
    let animationActive = sessionStorage.getItem('konamiActivated') === 'true';

    if (animationActive) {
        console.log("Animation déjà activée dans cette session.");
        activateThemeForCurrentMonth();
    }

    document.addEventListener('keydown', (event) => {
        if (event.key === konamiCode[konamiIndex]) {
            konamiIndex++;
            if (konamiIndex === konamiCode.length) {
                konamiCodeActivated();
                konamiIndex = 0;
            }
        } else {
            konamiIndex = 0;
        }
    });

    function konamiCodeActivated() {
        console.log("Konami Code activé !");
        sessionStorage.setItem('konamiActivated', 'true');
        animationActive = true;
        activateThemeForCurrentMonth();
    }

    function activateThemeForCurrentMonth() {
        const month = new Date().getMonth() + 1;
        let theme = 'default';
        let imageFilename = '';

        if (month === 12 || month === 1) {
            theme = 'winter';
            imageFilename = 'winter.jpg';
        } else if (month === 4 || month === 5) {
            theme = 'easter';
            imageFilename = 'easter.jpg';
        } else if (month === 10 || month === 11) {
            theme = 'autumn';
            imageFilename = 'autumn.jpg';
        } else if (month >= 6 && month <= 8) {
            theme = 'summer';
            imageFilename = 'summer.jpg';
        } else if (month == 2 || month == 3) {
            theme = 'carnival';
            imageFilename = 'carnival.jpg';
        } else if (month == 9) {
            theme = 'harvest';
            imageFilename = 'harvest.jpg';
        }

        addSeasonalImage(imageFilename);
        startSnowflakes(theme);
    }

    function addSeasonalImage(imageFilename) {
        const seasonalImage = document.getElementById('home_image');
        if (!seasonalImage) {
            console.warn("Warning : l'élément #home_image n'existe pas.");
            return;
        }
        // Note: URL will need to be set via a data attribute from Flask
        const staticUrl = seasonalImage.dataset.staticUrl || '/static/images/site/';
        seasonalImage.src = staticUrl + imageFilename;
    }

    function startSnowflakes(theme) {
        function createSnowflake(theme) {
            const snowflake = document.createElement('div');
            snowflake.classList.add('snowflake');

            let emojis = [];
            switch (theme) {
                case 'easter':
                    emojis = ['🥚', '🐣', '🐰', '🌸'];
                    break;
                case 'autumn':
                    emojis = ['🍂', '🍁', '🌰', '🎃'];
                    break;
                case 'summer':
                    emojis = ['☀️', '🏖️', '🍉', '🌴', '🦀', '🌊'];
                    break;
                case 'carnival':
                    emojis = ['🎭', '🎉', '🤹‍♂️', '🎺', '🎡'];
                    break;
                case 'harvest':
                    emojis = ['🌽', '🌾', '🍇', '🥖', '🍷'];
                    break;
                default:
                    emojis = ['❄'];
                    break;
            }

            snowflake.textContent = emojis[Math.floor(Math.random() * emojis.length)];
            snowflake.style.left = Math.random() * window.innerWidth + 'px';
            
            const size = Math.random() * 20 + 10;
            snowflake.style.fontSize = size + 'px';
            
            const duration = Math.random() * 5 + 3;
            snowflake.style.animationDuration = duration + 's';
            snowflake.style.opacity = Math.random();
            
            document.body.appendChild(snowflake);
            
            setTimeout(() => {
                snowflake.remove();
            }, duration * 1000);
        }

        setInterval(() => createSnowflake(theme), 200);
    }
})();

// Prevent Refresh Easter Egg
(function() {
    let refreshAttempts = 0;
    
    document.addEventListener("keydown", function (event) {
        if ((event.ctrlKey && event.key === "r") || event.key === "F5" || event.keyCode === 116) {
            event.preventDefault();
            refreshAttempts++;
            if (refreshAttempts === 1) {
                if (typeof showCustomAlert === 'function') {
                    const noRefreshImg = document.body.dataset.norefreshImage || '/static/images/site/norefresh.jpg';
                    showCustomAlert("Reloading the page is disabled.", noRefreshImg);
                }
            } else {
                if (typeof triggerDeathScreen === 'function') {
                    triggerDeathScreen(event, "Reloading the page is disabled !");
                }
                refreshAttempts = 0;
            }
        }
    });
})();

// Pixel Mode & Brol Mode
document.addEventListener("DOMContentLoaded", () => {
    const PIXEL_MODE_KEY = "pixelArtMode";
    const BROL_MODE_KEY = "brolMode";
    const secretWord = "pixel";
    let typedKeys = [];

    const tagsToScramble = ['h1', 'h3', 'h4', 'h5', 'h6', 'input'];

    function shuffleCambridgeWord(word) {
        if (word.length <= 3) return word;
        const first = word[0];
        const last = word[word.length - 1];
        let middle = word.slice(1, -1).split('');
        for (let i = middle.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [middle[i], middle[j]] = [middle[j], middle[i]];
        }
        return first + middle.join('') + last;
    }

    function shuffleCambridgeString(str) {
        return str.replace(/\w+/g, shuffleCambridgeWord);
    }

    function scrambleSelectedTags(scramble) {
        tagsToScramble.forEach(tag => {
            document.querySelectorAll(tag).forEach(el => {
                if (scramble) {
                    if (!el.dataset.originalText) el.dataset.originalText = el.textContent;
                    el.textContent = shuffleCambridgeString(el.dataset.originalText);
                } else if (el.dataset.originalText) {
                    el.textContent = el.dataset.originalText;
                }
            });
        });
    }

    function scrambleLooseTextNodes(parent, scramble) {
        for (let node of parent.childNodes) {
            if (node.nodeType === Node.TEXT_NODE && node.textContent.trim().length > 0) {
                if (!tagsToScramble.includes(node.parentNode.tagName?.toLowerCase())) {
                    if (scramble) {
                        if (!node.parentNode.dataset['originalText']) {
                            node.parentNode.dataset['originalText'] = node.textContent;
                        }
                        node.textContent = shuffleCambridgeString(node.parentNode.dataset['originalText']);
                    } else if (node.parentNode.dataset['originalText']) {
                        node.textContent = node.parentNode.dataset['originalText'];
                    }
                }
            } else if (node.nodeType === Node.ELEMENT_NODE) {
                scrambleLooseTextNodes(node, scramble);
            }
        }
    }

    function scrambleAllTexts(scramble) {
        scrambleSelectedTags(scramble);
        scrambleLooseTextNodes(document.body, scramble);
    }

    // Restore modes on initialization
    if (localStorage.getItem(PIXEL_MODE_KEY) === "true") {
        document.body.classList.add("pixel-art-mode");
    }
    if (localStorage.getItem(BROL_MODE_KEY) === "true") {
        document.body.classList.add("brol-mode");
        scrambleAllTexts(true);
    }

    document.addEventListener("keydown", (event) => {
        typedKeys.push(event.key.toLowerCase());
        typedKeys = typedKeys.slice(-secretWord.length);

        let pixelWord = (typedKeys.join("") === secretWord);
        let brolCombo = (event.ctrlKey && event.altKey && event.key.toLowerCase() === "b");

        if (pixelWord) {
            document.body.classList.remove("brol-mode");
            localStorage.setItem(BROL_MODE_KEY, "false");
            scrambleAllTexts(false);

            const isPixelActive = document.body.classList.toggle("pixel-art-mode");
            localStorage.setItem(PIXEL_MODE_KEY, isPixelActive.toString());
        }

        if (brolCombo) {
            document.body.classList.remove("pixel-art-mode");
            localStorage.setItem(PIXEL_MODE_KEY, "false");

            const isBrolActive = document.body.classList.toggle("brol-mode");
            localStorage.setItem(BROL_MODE_KEY, isBrolActive.toString());
            scrambleAllTexts(isBrolActive);

            if (isBrolActive && typeof showCustomAlert === 'function') {
                const noobImg = document.body.dataset.noobImage || '/static/images/site/noob.jpg';
                showCustomAlert('✨ Mode "Brol codé sur un coin de table" activé !', noobImg);
            }
        }
    });
});

// Death Screen
(function() {
    let typed = "";
    let targetPhrase = "YOU DIED";
    let audio = null;
    let deathTriggered = false;

    // Initialize audio when document is ready
    document.addEventListener("DOMContentLoaded", function() {
        const audioUrl = document.body.dataset.youDiedSound || '/static/sounds/site/you_died.mp3';
        audio = new Audio(audioUrl);
    });

    window.triggerDeathScreen = function(event, phrase) {
        if (deathTriggered) return;
        deathTriggered = true;

        if (!document.querySelector(".death-screen")) {
            let deathScreen = document.createElement("div");
            deathScreen.classList.add("death-screen");

            let textContainer = document.createElement("div");
            textContainer.classList.add("death-text-container");

            let textWrapper = document.createElement("div");
            textWrapper.classList.add("death-text-wrapper");

            let mainText = document.createElement("p");
            mainText.textContent = "YOU DIED";
            mainText.classList.add("death-text");

            textWrapper.appendChild(mainText);

            if (phrase) {
                let subText = document.createElement("p");
                subText.textContent = phrase;
                subText.classList.add("death-subtext");
                textWrapper.appendChild(subText);
            }

            textContainer.appendChild(textWrapper);
            deathScreen.appendChild(textContainer);
            document.body.appendChild(deathScreen);
        }

        let deathScreen = document.querySelector(".death-screen");
        document.body.style.backgroundColor = "black";
        deathScreen.classList.add("show-death");

        if (audio) audio.play();

        setTimeout(() => {
            document.body.style.backgroundColor = "";
            deathScreen.remove();
            deathTriggered = false;
        }, 9000);
    };

    document.addEventListener("keydown", function(event) {
        typed += event.key.toUpperCase();
        if (typed.length > targetPhrase.length) {
            typed = typed.slice(1);
        }

        if (typed === targetPhrase) {
            triggerDeathScreen(event, "");
        }
    });
})();
