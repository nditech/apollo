// includes bindings for fetching/fetched

var PaginatedCollection = Backbone.Collection.extend({
  initialize: function() {
    _.bindAll(this, 'parse', 'url', 'pageInfo', 'nextPage', 'previousPage', 'firstPage', 'lastPage', 'filtrate', 'sort_by');
    typeof(options) != 'undefined' || (options = {});
    typeof(this.limit) != 'undefined' || (this.limit = 20);
    typeof(this.offset) != 'undefined' || (this.offset = 0);
    typeof(this.filter_options) != 'undefined' || (this.filter_options = {});
    typeof(this.sort_field) != 'undefined' || (this.sort_field = '');
  },
  fetch: function(options) {
    typeof(options) != 'undefined' || (options = {});
    //this.trigger("fetching");
    var self = this;
    var success = options.success;
    options.success = function(resp) {
      //self.trigger("fetched");
      if(success) { success(self, resp); }
    };
    return Backbone.Collection.prototype.fetch.call(this, options);
  },
  parse: function(resp) {
    this.offset = resp.meta.offset;
    this.limit = resp.meta.limit;
    this.total = resp.meta.total_count;
    return resp.objects;
  },
  url: function() {
      urlparams = {offset: this.offset, limit: this.limit};
      urlparams = $.extend(urlparams, this.filter_options);
      if (this.sort_field) {
          urlparams = $.extend(urlparams, {order_by: this.sort_field});
      }
      return this.baseUrl + '?' + $.param(urlparams);
  },
  pageInfo: function() {
    var info = {
      total: this.total,
      offset: this.offset,
      page: Math.ceil(this.offset / this.limit) || 1,
      limit: this.limit,
      pages: Math.ceil(this.total / this.limit),
      prev: false,
      next: false
    };

    var max = Math.min(this.total, this.offset + this.limit);

    if (this.total == this.pages * this.limit) {
      max = this.total;
    }

    info.range = [(this.offset + 1), max];

    if (this.offset > 0) {
      info.prev = (this.offset - this.limit) || 1;
    }

    if (this.offset + this.limit < info.total) {
      info.next = this.offset + this.limit;
    }

    return info;
  },
  nextPage: function() {
    if (!this.pageInfo().next) {
      return false;
    }
    this.offset = this.offset + this.limit;
    return this.fetch();
  },
  previousPage: function() {
    if (!this.pageInfo().prev) {
      return false;
    }
    this.offset = (this.offset - this.limit) || 0;
    return this.fetch();
  },
  firstPage: function() {
    if (!this.pageInfo().page > 1) {
      return false;
    }
    this.offset = 0;
    return this.fetch();
  },
  lastPage: function() {
    if (!(this.pageInfo().page < this.pageInfo().pages)) {
      return false;
    }
    this.offset = ((this.pageInfo().pages - 1) * this.limit) || 0;
    return this.fetch();
  },
  filtrate: function (options) {
      this.filter_options = options || {};
      this.offset = 0;
      return this.fetch();
  },
  sort_by: function (field) {
      this.sort_field = field;
      this.offset = 0;
      return this.fetch();
  }

});