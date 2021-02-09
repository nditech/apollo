class APIClient {
  constructor(endpoints) {
    this.endpoints = endpoints;
  }

  _getResult = (response) => {
    let status = response.status;
    return {
      status: status,
      result: response.json()
    };
  };

  authenticate = (participant_id, password) => {
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

  refresh = (refreshToken) => {
    return fetch(this.endpoints.refresh, {
      headers: {
          'Authorization': `Bearer ${refreshToken}`,
          'Content-Type': 'application/json'
      },
      method: 'POST'
    }).then(this._getResult);
  };

  submit = (accessToken, formData) => {
    return fetch(this.endpoints.submit, {
      body: formData,
      headers: {
        'Authorization': `Bearer ${accessToken}`
      },
      method: 'POST'
    }).then(this._getResult);
  };

  getForms = (accessToken, events) => {
    const endpoint = (events === [] || events === undefined || events === null) ? this.endpoints.list : `${this.endpoints.list}?events=${events.join(',')}`;
    return fetch(endpoint, {
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json'
      }
    }).then(this._getResult);
  };

  logout = (accessToken) => {
    return fetch(this.endpoints.logout, {
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json'
      },
      method: 'DELETE'
    });
  }

  logout2 = (refreshToken) => {
    return fetch(this.endpoints.logout2, {
      headers: {
        'Authorization': `Bearer ${refreshToken}`,
        'Content-Type': 'application/json'
      },
      method: 'DELETE'
    });
  }
};
