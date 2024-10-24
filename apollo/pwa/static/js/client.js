class APIClient {
  constructor(endpoints) {
    this.endpoints = endpoints;
  }

  _getResult = function (response) {
    return {
      ok: response.ok,
      status: response.status,
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

  verify = function (uid, otp) {
    return fetch(this.endpoints.verify, {
      body: JSON.stringify({
        uid: uid,
        otp: otp
      }),
      headers: {
        'Content-Type': 'application/json',
      },
      method: 'POST'
    }).then(this._getResult);
  };

  resend = function (uid) {
    return fetch(this.endpoints.resend, {
      body: JSON.stringify({
        uid: uid
      }),
      headers: {
        'Content-Type': 'application/json'
      }
    }).then(this._getResult);
  }

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

  getForms = function () {
    return fetch(this.endpoints.list, {
      credentials: 'same-origin',
      headers: {
        'Content-Type': 'application/json'
      }
    }).then(this._getResult);
  };

  checkQAStatus = function (submissionUUID) {
    let endpoint = `${this.endpoints.qaStatus}${submissionUUID}`;
    return fetch(endpoint, {
      credentials: 'same-origin'
    }).then(this._getResult);
  }

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
