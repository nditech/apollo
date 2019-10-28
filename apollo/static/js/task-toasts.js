function setupTaskToasts(appSelector, taskNames, taskListUrl, eventStreamUrl) {
  var roundTo = function(num) {
    return Math.round((num + 0.00001) * 100) / 100;
  };

  Vue.component('task-toast', {
    updated: function() {
      // clear completed tasks
      if (this.taskInfo.quit == true)
        this.clear();
    },
    template: '#task-toast',
    props: {
      taskInfo: {
        id: String,
        status: String,
        quit: Boolean,
        progress: Object,
        description: String,
        name: String
      }
    },
    methods: {
      clear: function() {
        var self = this;
        setTimeout(function() {
          $(self.$el).toast('hide');
        }, 5000);
      }
    },
    computed: {
      processedCount: function() {
        return this.taskInfo.progress.processed_records;
      },
      warningCount: function() {
        return this.taskInfo.progress.warning_records;
      },
      errorCount: function() {
        return this.taskInfo.progress.error_records;
      },
      totalCount: function() {
        return this.taskInfo.progress.total_records;
      },
      processedStyle: function() {
        return {width: roundTo(100 * this.taskInfo.progress.processed_records / this.taskInfo.progress.total_records) + '%'};
      },
      warningStyle: function() {
        return {width: roundTo(100 * this.taskInfo.progress.warning_records / this.taskInfo.progress.total_records) + '%'};
      },
      errorStyle: function() {
        return {width: roundTo(100 * this.taskInfo.progress.error_records / this.taskInfo.progress.total_records) + '%'};
      }
    },
    mounted: function() {
      $(this.$el).toast('show');
      var self = this;
      if (this.taskInfo.quit == true) {
        self.clear();
      }
    },
    destroyed: function() {
      $(this.el).toast('dispose');
    }
  });

  var vm = new Vue({
    el: appSelector,
    data: {
      tasks: []
    },
    methods: {
      addTask: function(taskInfo) {
        // skip unregistered tasks
        if (taskNames.indexOf(taskInfo.name) === -1)
          return;

        var self = this;
        var index = self.tasks.findIndex(function(task) {
          return task.id == taskInfo.id;
        });
        if (index == -1)
          self.tasks.unshift(taskInfo);
        else
          self.tasks.splice(index, 1, taskInfo);
      },
      loadCompletedTasks: function() {
        var self = this;
        fetch(taskListUrl)
        .then(function(response) {
          return response.json();
        }).then(function(data) {
          if (data.results.length > 0) {
            data.results.forEach(function(taskInfo) {
              self.addTask(taskInfo);
            });
          }

        }).catch(function(err) {
          console.error(err);
        });
      },
      loadRunningTasks: function() {
        var self = this;
        if (window.EventSource) {
          var es = new EventSource(eventStreamUrl);
          es.onmessage = function (ev) {
            let data = JSON.parse(ev.data);
            if (data.id !== undefined) {
              self.addTask(data);
            }
          };
        }
      }
    },
    mounted: function() {
      this.loadCompletedTasks();
      this.loadRunningTasks();
    }
  });

  return vm;
}