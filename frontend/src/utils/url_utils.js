
export const url_utils = {
    generateFilterArgs(filters) {
        if (!filters) {
            return "";
        }
        let args = '?';
        for (var name in filters) {
            if (filters[name] !== null) {
                args += `&filter.${name}=${filters[name]}`
            }
        }
        return args;
    },

    elementVisibility(elementCss, show) {
        const els = document.querySelectorAll(elementCss);
        if (els && els.length > 0) {
            if (show) {
                els[0].style.visibility = 'visible';
            } else {
                els[0].style.visibility = 'hidden';
            }
        }
    }
};
