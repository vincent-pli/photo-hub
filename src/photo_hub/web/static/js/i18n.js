// i18n support for photo-hub
class I18n {
    constructor() {
        this.translations = {};
        this.currentLang = 'en';
        this.availableLangs = ['en', 'zh'];
        this.fallbackLang = 'en';
    }

    // Load translations for a language
    async loadLanguage(lang) {
        if (!this.availableLangs.includes(lang)) {
            console.warn(`Language ${lang} not supported, falling back to ${this.fallbackLang}`);
            lang = this.fallbackLang;
        }

        try {
            const response = await fetch(`/static/i18n/${lang}.json`);
            if (!response.ok) {
                throw new Error(`Failed to load translations for ${lang}`);
            }
            this.translations[lang] = await response.json();
            this.currentLang = lang;
            
            // Save preference to localStorage
            localStorage.setItem('photo-hub-language', lang);
            
            console.log(`Loaded translations for ${lang}`);
            return true;
        } catch (error) {
            console.error(`Failed to load translations for ${lang}:`, error);
            
            // Try to load fallback language
            if (lang !== this.fallbackLang) {
                return await this.loadLanguage(this.fallbackLang);
            }
            return false;
        }
    }

    // Get translation for a key
    t(key, params = {}) {
        const keys = key.split('.');
        let value = this.translations[this.currentLang];
        
        // Navigate through nested keys
        for (const k of keys) {
            if (value && typeof value === 'object' && k in value) {
                value = value[k];
            } else {
                // Try fallback language
                const fallbackValue = this.getFallbackValue(key);
                if (fallbackValue) {
                    value = fallbackValue;
                    break;
                }
                console.warn(`Translation key not found: ${key}`);
                return key; // Return the key itself as fallback
            }
        }
        
        // Handle arrays (for feature lists)
        if (Array.isArray(value)) {
            return value;
        }
        
        // Replace parameters in string
        if (typeof value === 'string') {
            return this.replaceParams(value, params);
        }
        
        return value || key;
    }

    // Get value from fallback language
    getFallbackValue(key) {
        if (this.currentLang === this.fallbackLang) {
            return null;
        }
        
        const keys = key.split('.');
        let value = this.translations[this.fallbackLang];
        
        for (const k of keys) {
            if (value && typeof value === 'object' && k in value) {
                value = value[k];
            } else {
                return null;
            }
        }
        
        return value;
    }

    // Replace {param} placeholders in strings
    replaceParams(str, params) {
        return str.replace(/\{(\w+)\}/g, (match, param) => {
            return params[param] !== undefined ? params[param] : match;
        });
    }

    // Get current language
    getLanguage() {
        return this.currentLang;
    }

    // Set language
    async setLanguage(lang) {
        if (lang === this.currentLang) {
            return true;
        }
        
        const success = await this.loadLanguage(lang);
        if (success) {
            // Dispatch language change event
            document.dispatchEvent(new CustomEvent('languageChanged', {
                detail: { language: lang }
            }));
        }
        return success;
    }

    // Initialize with preferred language
    async init() {
        // Try to get language from localStorage
        let preferredLang = localStorage.getItem('photo-hub-language');
        
        // If not in localStorage, try browser language
        if (!preferredLang) {
            const browserLang = navigator.language || navigator.userLanguage;
            if (browserLang.startsWith('zh')) {
                preferredLang = 'zh';
            } else {
                preferredLang = 'en';
            }
        }
        
        // Ensure language is supported
        if (!this.availableLangs.includes(preferredLang)) {
            preferredLang = this.fallbackLang;
        }
        
        return await this.loadLanguage(preferredLang);
    }

    // Format date in current language
    formatDate(date) {
        return new Date(date).toLocaleString(this.currentLang);
    }
}

// Create global i18n instance
window.i18n = new I18n();