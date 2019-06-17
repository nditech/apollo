window.LocationOptions = {
    width: 'null',
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

window.ParticipantOptions = {
    width: 'null',
    theme: 'bootstrap4',
    minimumInputLength: 1,
    allowClear: true,
    placeholder: {
        id: '__None',
        text: 'Participant'
    },
    ajax: {
        url: '/api/participants/',
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
    templateResult: function (participant) {
        if (participant.participant_id) {
            return safe_string(participant.participant_id) + ' · ' + safe_string(participant.name);
        } else {
            return safe_string(participant.text);
        }
    },
    templateSelection: function (participant) {
        if (participant.participant_id) {
            return safe_string(participant.participant_id) + ' · ' + safe_string(participant.name);
        } else {
            return safe_string(participant.text);
        }
    },
    escapeMarkup: function (m) { return m; }
};

window.safe_string = function (v) {
    return $('<textarea />').text(v).html();
}