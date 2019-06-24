(function() {
  angular.module("builder.components", ["builder", "validator.rules"]).config([
    "$builderProvider", function($builderProvider) {
      $builderProvider.registerComponent("group", {
        group: "Default",
        label: "Section",
        description: "description",
        placeholder: "",
        required: false,
        template:
        `<div class="card border-light bg-light mb-2">
          <h6 class="card-header">{{label}}</h6>
        </div>`,
        popoverTemplate:
        `<form>
          <div class="form-group mb-2">
            <label class="control-label">Name</label>
            <input type="text" ng-model="label" class="form-control"/>
          </div>
          <div class="form-group mb-2 mt-4 text-right">
            <input type="button" ng-click="popover.remove($event)" class="btn btn-danger mr-1" value="Delete"/>
            <input type="button" ng-click="popover.cancel($event)" class="btn btn-secondary mr-1" value="Cancel"/>
            <input type="submit" ng-click="popover.save($event)" class="btn btn-primary" value="Save"/>
          </div>
        </form>`
      });
      $builderProvider.registerComponent("textInput", {
        group: "Default",
        label: "AA",
        description: "Numeric Question",
        placeholder: "",
        required: false,
        min: 0,
        max: 9999,
        template:
        `<div class="form-group row">
          <label for="{{formName+index}}" class="col-sm-3 control-label text-right mt-2" ng-class="{'fb-required':required}">{{label}}</label>
          <div class="col-sm-8">
            <input type="text" ng-model="inputText" validator-required="{{required}}" validator-group="{{formName}}" id="{{formName+index}}" class="form-control" placeholder="{{placeholder}}"/>
            <p class="form-text">{{description}}</p>
          </div>
        </div>`,
        popoverTemplate:
        `<form>
          <div class="form-group mb-2">
            <label class="control-label">Name</label>
            <input type="text" ng-model="label" class="form-control"/>
          </div>
          <div class="form-group mb-2">
            <label class="control-label">Description</label>
            <input type="text" ng-model="description" class="form-control"/>
          </div>
          <div class="form-group mb-2">
            <label class="control-label">Minimum</label>
            <input type="text" ng-model="min" class="form-control" value="0" />
          </div>
          <div class="form-group mb-2">
            <label class="control-label">Maximum</label>
            <input type="text" ng-model="max" class="form-control" value="9999" />
          </div>
          <div class="custom-control custom-checkbox mb-2 mt-3">
            <input type="checkbox" id="required" class="custom-control-input" ng-model="required">
            <label class="custom-control-label" for="required">Mark as true if present?</label>
          </div>
          <div class="form-group mb-2">
            <label class="control-label">Analysis</label>
            <select ng-model="analysis" ng-options="obj.value as obj.option for obj in analysisOptions" class="form-control custom-select"></select>
          </div>
          <div class="form-group mb-2" ng-if="validationOptions.length > 0">
            <label class="control-label">Validation</label>
            <select ng-model="$parent.validation" class="form-control custom-select" ng-options="option.rule as option.label for option in validationOptions"></select>
          </div>
          <div class="form-group mb-2 mt-4 text-right">
            <input type="button" ng-click="popover.remove($event)" class="btn btn-danger mr-1" value="Delete"/>
            <input type="button" ng-click="popover.cancel($event)" class="btn btn-secondary mr-1" value="Cancel"/>
            <input type="submit" ng-click="popover.save($event)" class="btn btn-primary" value="Save"/>
          </div>
        </form>`
      });
      $builderProvider.registerComponent("radio", {
        group: "Default",
        label: "AA",
        description: "Single Choice Question",
        placeholder: "",
        required: false,
        options: ["Option 1", "Option 2"],
        template:
        `<div class="form-group row">
          <label for="{{formName+index}}" class="col-sm-3 control-label text-right mt-2" ng-class="{'fb-required':required}">{{label}}</label>
          <div class="col-sm-8">
            <div class="custom-control custom-radio" ng-repeat="item in options track by $index">
              <input id="{{formName+index}}" name="{{formName+index}}" class="custom-control-input" ng-model="$parent.inputText" validator-group="{{formName}}" value="{{item}}" type="radio"/>
              <label class="custom-control-label" for="{{formName+index}}">{{item}}</label>
            </div>
            <p class="form-text">{{description}}</p>
          </div>
        </div>`,
        popoverTemplate:
        `<form>
          <div class="form-group mb-2">
            <label class="control-label">Name</label>
            <input type="text" ng-model="label" class="form-control"/>
          </div>
          <div class="form-group mb-2">
            <label class="control-label">Description</label>
            <input type="text" ng-model="description" class="form-control"/>
          </div>
          <div class="form-group mb-2">
            <label class="control-label">Options</label>
            <textarea class="form-control" rows="3" ng-model="optionsText"/>
          </div>
          <div class="form-group mb-2">
            <label class="control-label">Analysis</label>
            <select ng-model="analysis" ng-options="obj.value as obj.option for obj in analysisOptions" class="form-control custom-select"></select>
          </div>
          <div class="form-group mb-2" ng-if="validationOptions.length > 0">
            <label class="control-label">Validation</label>
            <select ng-model="$parent.validation" class="form-control custom-select" ng-options="option.rule as option.label for option in validationOptions"></select>
          </div>
          <div class="form-group mb-2 mt-4 text-right">
            <input type="button" ng-click="popover.remove($event)" class="btn btn-danger mr-1" value="Delete"/>
            <input type="button" ng-click="popover.cancel($event)" class="btn btn-secondary mr-1" value="Cancel"/>
            <input type="submit" ng-click="popover.save($event)" class="btn btn-primary" value="Save"/>
          </div>
        </form>`
      });
      
      $builderProvider.registerComponent("checkbox", {
        group: "Default",
        label: "AA",
        description: "Multiple Choices Question",
        placeholder: "",
        required: false,
        options: ["Option 1", "Option 2"],
        arrayToText: true,
        template:
        `<div class="form-group row">
          <label for="{{formName+index}}" class="col-sm-3 control-label text-right mt-2" ng-class="{'fb-required':required}">{{label}}</label>
          <div class="col-sm-8">
            <div class="custom-control custom-checkbox" ng-repeat="item in options track by $index">
              <input id="{{formName+index}}" name="{{formName+index}}" class="custom-control-input" ng-model="$parent.inputText" validator-group="{{formName}}" value="{{item}}" type="checkbox"/>
              <label class="custom-control-label" for="{{formName+index}}">{{item}}</label>
            </div>
            <p class="form-text">{{description}}</p>
          </div>
        </div>`,
        popoverTemplate:
        `<form>
          <div class="form-group mb-2">
            <label class="control-label">Name</label>
            <input type="text" ng-model="label" class="form-control"/>
          </div>
          <div class="form-group mb-2">
            <label class="control-label">Description</label>
            <input type="text" ng-model="description" class="form-control"/>
          </div>
          <div class="form-group mb-2">
            <label class="control-label">Options</label>
            <textarea class="form-control" rows="3" ng-model="optionsText"/>
          </div>
          <div class="form-group mb-2">
            <label class="control-label">Analysis</label>
            <select ng-model="analysis" ng-options="obj.value as obj.option for obj in analysisOptions" class="form-control custom-select"></select>
          </div>
          <div class="form-group mb-2 mt-4 text-right">
            <input type="button" ng-click="popover.remove($event)" class="btn btn-danger mr-1" value="Delete"/>
            <input type="button" ng-click="popover.cancel($event)" class="btn btn-secondary mr-1" value="Cancel"/>
            <input type="submit" ng-click="popover.save($event)" class="btn btn-primary" value="Save"/>
          </div>
        </form>`
      });

      return $builderProvider.registerComponent("textarea", {
        group: "Default",
        label: "Comment",
        description: "Comment Question",
        placeholder: "",
        required: false,
        template:
        `<div class="form-group row">
          <label for="{{formName+index}}" class="col-sm-3 control-label text-right mt-2" ng-class="{'fb-required':required}">{{label}}</label>
          <div class="col-sm-8">
            <textarea ng-model="inputText" rows="1" validator-required="{{required}}" validator-group="{{formName}}" id="{{formName+index}}" class="form-control" placeholder="{{placeholder}}"></textarea>
            <p class="form-text">{{description}}</p>
          </div>
        </div>`,
        popoverTemplate:
        `<form>
          <div class="form-group mb-2">
            <label class="control-label">Name</label>
            <input type="text" ng-model="label" class="form-control"/>
          </div>
          <div class="form-group mb-2">
            <label class="control-label">Description</label>
            <input type="text" ng-model="description" class="form-control"/>
          </div>
          <div class="custom-control custom-checkbox mb-2 mt-3">
            <input type="checkbox" id="required" class="custom-control-input" ng-model="required">
            <label class="custom-control-label" for="required">Mark as true if present?</label>
          </div>
          <div class="form-group mb-2">
            <label class="control-label">Analysis</label>
            <select ng-model="analysis" ng-options="obj.value as obj.option for obj in analysisOptions" class="form-control custom-select"></select>
          </div>
          <div class="form-group mb-2" ng-if="validationOptions.length > 0">
            <label class="control-label">Validation</label>
            <select ng-model="$parent.validation" class="form-control custom-select" ng-options="option.rule as option.label for option in validationOptions"></select>
          </div>
          <div class="form-group mb-2 mt-4 text-right">
            <input type="button" ng-click="popover.remove($event)" class="btn btn-danger mr-1" value="Delete"/>
            <input type="button" ng-click="popover.cancel($event)" class="btn btn-secondary mr-1" value="Cancel"/>
            <input type="submit" ng-click="popover.save($event)" class="btn btn-primary" value="Save"/>
          </div>
        </form>`
      });
    }
  ]);
}).call(this);
