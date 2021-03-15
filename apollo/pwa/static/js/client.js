class APIClient {
  constructor(endpoints) {
    this.endpoints = endpoints;
  }

  _getResult = function (response) {
    let status = response.status;
    return {
      status: status,
      result: response.json()
    };
  };

  authenticate = function (participant_id, password) {
    return fetch(this.endpoints.login, {
      body: JSON.stringify({
        participant_id: participant_id,
        password: password
      }),
      headers: {
        'Content-Type': 'application/json'
      },
      method: 'POST'
      }).then(this._getResult);
  };

  submit = function (formData, csrf_token) {
    return fetch(this.endpoints.submit, {
      body: formData,
      credentials: 'same-origin',
      headers: {
        'X-CSRF-TOKEN': csrf_token
      },
      method: 'POST'
    }).then(this._getResult);
  };

  getForms = function (events) {
    const endpoint = (events === [] || events === undefined || events === null) ? this.endpoints.list : `${this.endpoints.list}?events=${events.join(',')}`;
    return fetch(endpoint, {
      credentials: 'same-origin',
      headers: {
        'Content-Type': 'application/json'
      }
    }).then(this._getResult);
  };

  logout = function (csrf_token) {
    return fetch(this.endpoints.logout, {
      credentials: 'same-origin',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRF-TOKEN': csrf_token
      },
      method: 'DELETE'
    });
  }
};
