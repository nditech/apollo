(function() {
  angular.module('builder.components', ['builder', 'validator.rules']).config([
    '$builderProvider', function($builderProvider) {
      $builderProvider.registerComponent('group', {
        group: 'Default',
        label: 'Section',
        description: 'description',
        placeholder: '',
        required: false,
        template: "<div class=\"panel panel-default\">\n    <div class=\"panel-heading\">{{label}}</div>\n    </div>",
        popoverTemplate: "<form>\n    <div class=\"form-group\">\n    <label class='control-label'>Name</label>\n    <input type='text' ng-model=\"label\" class='form-control'/>\n    </div>\n    <div class='form-group'>\n        <input type='submit' ng-click=\"popover.save($event)\" class='btn btn-primary' value='Save'/>\n        <input type='button' ng-click=\"popover.cancel($event)\" class='btn btn-default' value='Cancel'/>\n        <input type='button' ng-click=\"popover.remove($event)\" class='btn btn-danger' value='Delete'/>\n    </div>\n</form>"
      });
      $builderProvider.registerComponent('textInput', {
        group: 'Default',
        label: 'AA',
        description: 'Numeric Question',
        placeholder: '',
        required: false,
        min: 0,
        max: 9999,
        template: "<div class=\"form-group\">\n    <label for=\"{{formName+index}}\" class=\"col-sm-2 control-label\" ng-class=\"{'fb-required':required}\">{{label}}</label>\n    <div class=\"col-sm-10\">\n        <input type=\"text\" ng-model=\"inputText\" validator-required=\"{{required}}\" validator-group=\"{{formName}}\" id=\"{{formName+index}}\" class=\"form-control\" placeholder=\"{{placeholder}}\"/>\n        <p class='help-block'>{{description}}</p>\n    </div>\n</div>",
        popoverTemplate: "<form>\n    <div class=\"form-group\">\n        <label class='control-label'>Name</label>\n        <input type='text' ng-model=\"label\" class='form-control'/>\n    </div>\n    <div class=\"form-group\">\n        <label class='control-label'>Description</label>\n        <input type='text' ng-model=\"description\" class='form-control'/>\n    </div>\n    <div class=\"form-group\">\n        <label class='control-label'>Minimum</label>\n        <input type='text' ng-model=\"min\" class='form-control' value='0' />\n    </div>\n    <div class=\"form-group\">\n        <label class='control-label'>Maximum</label>\n        <input type='text' ng-model=\"max\" class='form-control' value='9999' />\n    </div>\n    <div class=\"checkbox\">\n        <label>\n            <input type='checkbox' ng-model=\"required\" />\n            Mark as true if present?</label>\n    </div>\n    <div class=\"form-group\">\n        <label class='control-label'>Analysis</label>\n        <select ng-model=\"analysis\" ng-options=\"obj.value as obj.option for obj in analysisOptions\" class='form-control'></select>\n    </div>\n    <div class=\"form-group\" ng-if=\"validationOptions.length > 0\">\n        <label class='control-label'>Validation</label>\n        <select ng-model=\"$parent.validation\" class='form-control' ng-options=\"option.rule as option.label for option in validationOptions\"></select>\n    </div>\n\n    <hr/>\n    <div class='form-group'>\n        <input type='submit' ng-click=\"popover.save($event)\" class='btn btn-primary' value='Save'/>\n        <input type='button' ng-click=\"popover.cancel($event)\" class='btn btn-default' value='Cancel'/>\n        <input type='button' ng-click=\"popover.remove($event)\" class='btn btn-danger' value='Delete'/>\n    </div>\n</form>"
      });
      $builderProvider.registerComponent('radio', {
        group: 'Default',
        label: 'AA',
        description: 'Single Choice Question',
        placeholder: '',
        required: false,
        options: ['Option 1', 'Option 2'],
        template: "<div class=\"form-group\">\n    <label for=\"{{formName+index}}\" class=\"col-sm-2 control-label\" ng-class=\"{'fb-required':required}\">{{label}}</label>\n    <div class=\"col-sm-10\">\n        <div class='radio' ng-repeat=\"item in options track by $index\">\n            <label><input name='{{formName+index}}' ng-model=\"$parent.inputText\" validator-group=\"{{formName}}\" value='{{item}}' type='radio'/>\n                {{item}}\n            </label>\n        </div>\n        <p class='help-block'>{{description}}</p>\n    </div>\n</div>",
        popoverTemplate: "<form>\n    <div class=\"form-group\">\n        <label class='control-label'>Name</label>\n        <input type='text' ng-model=\"label\" class='form-control'/>\n    </div>\n    <div class=\"form-group\">\n        <label class='control-label'>Description</label>\n        <input type='text' ng-model=\"description\" class='form-control'/>\n    </div>\n    <div class=\"form-group\">\n        <label class='control-label'>Options</label>\n        <textarea class=\"form-control\" rows=\"3\" ng-model=\"optionsText\"/>\n    </div>\n    <div class=\"form-group\">\n        <label class='control-label'>Analysis</label>\n        <select ng-model=\"analysis\" ng-options=\"obj.value as obj.option for obj in analysisOptions\" class='form-control'></select>\n    </div>\n\n    <hr/>\n    <div class='form-group'>\n        <input type='submit' ng-click=\"popover.save($event)\" class='btn btn-primary' value='Save'/>\n        <input type='button' ng-click=\"popover.cancel($event)\" class='btn btn-default' value='Cancel'/>\n        <input type='button' ng-click=\"popover.remove($event)\" class='btn btn-danger' value='Delete'/>\n    </div>\n</form>"
      });
      
      $builderProvider.registerComponent('checkbox', {
        group: 'Default',
        label: 'AA',
        description: 'Multiple Choices Question',
        placeholder: '',
        required: false,
        options: ['Option 1', 'Option 2'],
        arrayToText: true,
        template: "<div class=\"form-group\">\n    <label for=\"{{formName+index}}\" class=\"col-sm-2 control-label\" ng-class=\"{'fb-required':required}\">{{label}}</label>\n    <div class=\"col-sm-10\">\n        <input type='hidden' ng-model=\"inputText\" validator-required=\"{{required}}\" validator-group=\"{{formName}}\"/>\n        <div class='checkbox' ng-repeat=\"item in options track by $index\">\n            <label><input type='checkbox' ng-model=\"$parent.inputArray[$index]\" value='item'/>\n                {{item}}\n            </label>\n        </div>\n        <p class='help-block'>{{description}}</p>\n    </div>\n</div>",
        // popoverTemplate: "<form>\n    <div class=\"form-group\">\n        <label class='control-label'>Name</label>\n        <input type='text' ng-model=\"label\" validator=\"[required]\" class='form-control'/>\n    </div>\n    <div class=\"form-group\">\n        <label class='control-label'>Description</label>\n        <input type='text' ng-model=\"description\" class='form-control'/>\n    </div>\n    <div class=\"form-group\">\n        <label class='control-label'>Options</label>\n        <textarea class=\"form-control\" rows=\"3\" ng-model=\"optionsText\"/>\n    </div>\n\n    <hr/>\n    <div class='form-group'>\n        <input type='submit' ng-click=\"popover.save($event)\" class='btn btn-primary' value='Save'/>\n        <input type='button' ng-click=\"popover.cancel($event)\" class='btn btn-default' value='Cancel'/>\n        <input type='button' ng-click=\"popover.remove($event)\" class='btn btn-danger' value='Delete'/>\n    </div>\n</form>"
        popoverTemplate: "<form>\n    <div class=\"form-group\">\n        <label class='control-label'>Name</label>\n        <input type='text' ng-model=\"label\" class='form-control'/>\n    </div>\n    <div class=\"form-group\">\n        <label class='control-label'>Description</label>\n        <input type='text' ng-model=\"description\" class='form-control'/>\n    </div>\n    <div class=\"form-group\">\n        <label class='control-label'>Options</label>\n        <textarea class=\"form-control\" rows=\"3\" ng-model=\"optionsText\"/>\n    </div>\n    <div class=\"form-group\">\n        <label class='control-label'>Analysis</label>\n        <select ng-model=\"analysis\" ng-options=\"obj.value as obj.option for obj in analysisOptions\" class='form-control'></select>\n    </div>\n\n    <hr/>\n    <div class='form-group'>\n        <input type='submit' ng-click=\"popover.save($event)\" class='btn btn-primary' value='Save'/>\n        <input type='button' ng-click=\"popover.cancel($event)\" class='btn btn-default' value='Cancel'/>\n        <input type='button' ng-click=\"popover.remove($event)\" class='btn btn-danger' value='Delete'/>\n    </div>\n</form>"
      });

      return $builderProvider.registerComponent('textarea', {
        group: 'Default',
        label: 'Comment',
        description: 'Comment Question',
        placeholder: '',
        required: false,
        template: "<div class=\"form-group\">\n    <label for=\"{{formName+index}}\" class=\"col-sm-2 control-label\" ng-class=\"{'fb-required':required}\">{{label}}</label>\n    <div class=\"col-sm-10\">\n        <textarea ng-model=\"inputText\" rows=\"1\" validator-required=\"{{required}}\" validator-group=\"{{formName}}\" id=\"{{formName+index}}\" class=\"form-control\" placeholder=\"{{placeholder}}\"/>\n        <p class='help-block'>{{description}}</p>\n    </div>\n</div>",
        popoverTemplate: "<form>\n    <div class=\"form-group\">\n        <label class='control-label'>Name</label>\n        <input type='text' ng-model=\"label\" class='form-control'/>\n    </div>\n    <div class=\"form-group\">\n        <label class='control-label'>Description</label>\n        <input type='text' ng-model=\"description\" class='form-control'/>\n    </div>\n    <div class=\"checkbox\">\n        <label>\n            <input type='checkbox' ng-model=\"required\" />\n            Mark as true if present?</label>\n    </div>\n    <div class=\"form-group\">\n        <label class='control-label'>Analysis</label>\n        <select ng-model=\"analysis\" ng-options=\"obj.value as obj.option for obj in analysisOptions\" class='form-control'></select>\n    </div>\n    <div class=\"form-group\" ng-if=\"validationOptions.length > 0\">\n        <label class='control-label'>Validation</label>\n        <select ng-model=\"$parent.validation\" class='form-control' ng-options=\"option.rule as option.label for option in validationOptions\"></select>\n    </div>\n\n    <hr/>\n    <div class='form-group'>\n        <input type='submit' ng-click=\"popover.save($event)\" class='btn btn-primary' value='Save'/>\n        <input type='button' ng-click=\"popover.cancel($event)\" class='btn btn-default' value='Cancel'/>\n        <input type='button' ng-click=\"popover.remove($event)\" class='btn btn-danger' value='Delete'/>\n    </div>\n</form>"
      });
    }
  ]);
}).call(this);
