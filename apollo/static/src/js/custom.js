window.LocationOptions = {
    theme: 'bootstrap4',
    minimumInputLength: 1,
    placeholder: {
        id: '-1',
        text: 'Location'
    },
    ajax: {
        url: '/api/locations/',
        dataType: 'json',
        delay: 500,
        data: function (params) {
            return {
                q: params.term,
                limit: 20,
                offset: (params.page - 1) * 20 || 0
            };
        },
        processResults: function (data, params) {
            return {
                results: data.objects,
                pagination: {
                    more: (params.page * 20) < data.meta.total
                }
            };
        }
    },
    templateResult: function (location) {
        if (location.location_type) {
            return safe_string(location.name) + ' · ' + safe_string(location.location_type);
        } else {
            return safe_string(location.text);
        }
    },
    templateSelection: function (location) {
        if (location.location_type) {
            return safe_string(location.name) + ' · ' + safe_string(location.location_type);
        } else {
            return safe_string(location.text);
        }
    },
    escapeMarkup: function (m) { return m; }
};

window.safe_string = function (v) {
    return $('<textarea />').text(v).html();
}