/* Rewrite changelog category headings */
document.addEventListener('DOMContentLoaded', function () {
    const map = {
        'Feat': '✨ Features',
        'Fix': '🔧 Bug Fixes',
		'Docs': '📚 Documentation',
		'Chore': '🧹 Chores',
		'Refactor': '🛠 Refactors',
		'Test': '🧪 Tests',
		'CI': '🤖 CI',
		'Perf': '⚡ Performance',
		'Build': '🏗 Build',
		'Style': '🎨 Styles',
    };

    document.querySelectorAll('h3').forEach(function (h3) {
        const text = h3.childNodes[0];
        if (text && text.nodeType === Node.TEXT_NODE) {
            const trimmed = text.textContent.trim();
            if (map[trimmed]) {
                text.textContent = ' ' + map[trimmed] + ' ';
            }
        }
    });
});
