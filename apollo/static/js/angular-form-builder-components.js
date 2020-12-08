(function() {
  angular.module("builder.components", ["builder", "validator.rules"]).config([
    "$builderProvider", function($builderProvider) {
      $builderProvider.registerComponent("group", {
        group: "Default",
        label: i18n.gettext("Section"),
        description: "description",
        placeholder: "",
        required: false,
        template:
        `<div class="card border-light bg-light mb-1">
          <h6 class="card-header">{{label}}</h6>
        </div>`,
        popoverTemplate:
        `<form>
          <div class="form-group mb-2">
            <label class="control-label">{{nameLabel}}</label>
            <input type="text" ng-model="label" class="form-control"/>
          </div>
          <div class="form-group mb-2 mt-4 text-right">
            <input type="button" ng-click="popover.remove($event)" class="btn btn-danger mr-1" value="{{deleteLabel}}"/>
            <input type="button" ng-click="popover.cancel($event)" class="btn btn-secondary mr-1" value="{{cancelLabel}}"/>
            <input type="submit" ng-click="popover.save($event)" class="btn btn-primary" value="{{saveLabel}}"/>
          </div>
        </form>`
      });
      $builderProvider.registerComponent("textInput", {
        group: "Default",
        label: "AA",
        description: i18n.gettext("Numeric Question"),
        placeholder: "",
        required: false,
        min: 0,
        max: 9999,
        subtype: 'integer',
        expected: 0,
        template:
        `<div class="form-group row">
          <label for="{{label}}" class="col-3 control-label text-right mt-1" ng-class="{'fb-required':required}">{{label}}</label>
          <div class="col-8">
            <input type="text" ng-model="inputText" validator-required="{{required}}" validator-group="{{formName}}" id="{{label}}" class="form-control" placeholder="{{placeholder}}"/>
            <p class="form-text mb-1">{{description}}</p>
          </div>
        </div>`,
        popoverTemplate:
        `<form>
          <div class="form-group mb-2">
            <label class="control-label">{{nameLabel}}</label>
            <input type="text" ng-model="label" class="form-control"/>
          </div>
          <div class="form-group mb-2">
            <label class="control-label">{{descriptionLabel}}</label>
            <input type="text" ng-model="description" class="form-control"/>
          </div>
          <div class="form-group mb-2">
            <label class="control-label">{{minimumLabel}}</label>
            <input type="text" ng-model="min" class="form-control" value="0" />
          </div>
          <div class="form-group mb-2">
            <label class="control-label">{{maximumLabel}}</label>
            <input type="text" ng-model="max" class="form-control" value="9999" />
          </div>
          <div class="form-group mb-2">
            <label class="control-label">{{typeLabel}}</label>
            <select ng-model="subtype" ng-options="obj.value as obj.option for obj in subtypeOptions" class="form-control custom-select"></select>
          </div>
          <div class="form-group mb-2">
            <label class="control-label">{{analysisLabel}}</label>
            <select ng-model="analysis" ng-options="obj.value as obj.option for obj in getAnalysisOptions('textInput', subtype)" class="form-control custom-select"></select>
          </div>
          <div class="form-group mb-2" ng-show="analysis == 'bucket'">
            <label class="control-label">{{expectedValueLabel}}</label>
            <input type="text" ng-model="expected" class="form-control" />
          </div>
          <div class="form-group mb-2" ng-if="validationOptions.length > 0">
            <label class="control-label">{{validationLabel}}</label>
            <select ng-model="$parent.validation" class="form-control custom-select" ng-options="option.rule as option.label for option in validationOptions"></select>
          </div>
          <div class="form-group mb-2 mt-4 text-right">
            <input type="button" ng-click="popover.remove($event)" class="btn btn-danger mr-1" value="{{deleteLabel}}"/>
            <input type="button" ng-click="popover.cancel($event)" class="btn btn-secondary mr-1" value="{{cancelLabel}}"/>
            <input type="submit" ng-click="popover.save($event)" class="btn btn-primary" value="{{saveLabel}}"/>
          </div>
        </form>`
      });
      $builderProvider.registerComponent("radio", {
        group: "Default",
        label: "BB",
        description: i18n.gettext("Single Choice Question"),
        placeholder: "",
        required: false,
        options: [i18n.gettext("Option 1"), i18n.gettext("Option 2")],
        template:
        `<div class="form-group row">
          <label for="{{label}}" class="col-3 control-label text-right mt-1" ng-class="{'fb-required':required}">{{label}}</label>
          <div class="col-8">
            <div class="custom-control custom-radio" ng-repeat="item in options track by $index">
              <input id="{{label}}" name="{{label}}" class="custom-control-input" ng-model="$parent.inputText" validator-group="{{formName}}" value="{{item}}" type="radio"/>
              <label class="custom-control-label" for="{{label+$index}}">{{item}}</label>
            </div>
            <p class="form-text mb-1">{{description}}</p>
          </div>
        </div>`,
        popoverTemplate:
        `<form>
          <div class="form-group mb-2">
            <label class="control-label">{{nameLabel}}</label>
            <input type="text" ng-model="label" class="form-control"/>
          </div>
          <div class="form-group mb-2">
            <label class="control-label">{{descriptionLabel}}</label>
            <input type="text" ng-model="description" class="form-control"/>
          </div>
          <div class="form-group mb-2">
            <label class="control-label">{{optionsLabel}}</label>
            <textarea class="form-control" rows="3" ng-model="optionsText"/>
          </div>
          <div class="form-group mb-2">
            <label class="control-label">{{analysisLabel}}</label>
            <select ng-model="analysis" ng-options="obj.value as obj.option for obj in getAnalysisOptions('radio', null)" class="form-control custom-select"></select>
          </div>
          <div class="form-group mb-2" ng-if="validationOptions.length > 0">
            <label class="control-label">{{validationLabel}}</label>
            <select ng-model="$parent.validation" class="form-control custom-select" ng-options="option.rule as option.label for option in validationOptions"></select>
          </div>
          <div class="form-group mb-2 mt-4 text-right">
            <input type="button" ng-click="popover.remove($event)" class="btn btn-danger mr-1" value="{{deleteLabel}}"/>
            <input type="button" ng-click="popover.cancel($event)" class="btn btn-secondary mr-1" value="{{cancelLabel}}"/>
            <input type="submit" ng-click="popover.save($event)" class="btn btn-primary" value="{{saveLabel}}"/>
          </div>
        </form>`
      });
      $builderProvider.registerComponent("yesno", {
        group: "Default",
        label: "CC",
        description: i18n.gettext("Yes/No Question"),
        placeholder: "",
        required: false,
        options: [i18n.gettext("Yes"), i18n.gettext("No")],
        template:
          `<div class="form-group row">
          <label for="{{label}}" class="col-3 control-label text-right mt-1" ng-class="{'fb-required':required}">{{label}}</label>
          <div class="col-8">
            <div class="custom-control custom-radio" ng-repeat="item in options track by $index">
              <input id="{{label}}" name="{{label}}" class="custom-control-input" ng-model="$parent.inputText" validator-group="{{formName}}" value="{{item}}" type="radio"/>
              <label class="custom-control-label" for="{{label+$index}}">{{item}}</label>
            </div>
            <p class="form-text mb-1">{{description}}</p>
          </div>
        </div>`,
        popoverTemplate:
          `<form>
          <div class="form-group mb-2">
            <label class="control-label">{{nameLabel}}</label>
            <input type="text" ng-model="label" class="form-control"/>
          </div>
          <div class="form-group mb-2">
            <label class="control-label">{{descriptionLabel}}</label>
            <input type="text" ng-model="description" class="form-control"/>
          </div>
          <div class="form-group mb-2">
            <label class="control-label">{{optionsLabel}}</label>
            <textarea class="form-control" rows="3" ng-model="optionsText"/>
          </div>
          <div class="form-group mb-2">
            <label class="control-label">{{analysisLabel}}</label>
            <select ng-model="analysis" ng-options="obj.value as obj.option for obj in getAnalysisOptions('yesno', null)" class="form-control custom-select"></select>
          </div>
          <div class="form-group mb-2" ng-if="validationOptions.length > 0">
            <label class="control-label">{{validationLabel}}</label>
            <select ng-model="$parent.validation" class="form-control custom-select" ng-options="option.rule as option.label for option in validationOptions"></select>
          </div>
          <div class="form-group mb-2 mt-4 text-right">
            <input type="button" ng-click="popover.remove($event)" class="btn btn-danger mr-1" value="{{deleteLabel}}"/>
            <input type="button" ng-click="popover.cancel($event)" class="btn btn-secondary mr-1" value="{{cancelLabel}}"/>
            <input type="submit" ng-click="popover.save($event)" class="btn btn-primary" value="{{saveLabel}}"/>
          </div>
        </form>`
      });
      
      $builderProvider.registerComponent("checkbox", {
        group: "Default",
        label: "DD",
        description: i18n.gettext("Multiple Choice Question"),
        placeholder: "",
        required: false,
        options: [i18n.gettext("Option 1"), i18n.gettext("Option 2")],
        arrayToText: true,
        template:
        `<div class="form-group row">
          <label for="{{label}}" class="col-3 control-label text-right mt-1" ng-class="{'fb-required':required}">{{label}}</label>
          <div class="col-8">
            <div class="custom-control custom-checkbox" ng-repeat="item in options track by $index">
              <input id="{{label}}" name="{{label}}" class="custom-control-input" ng-model="$parent.inputText" validator-group="{{formName}}" value="{{item}}" type="checkbox"/>
              <label class="custom-control-label" for="{{label+$index}}">{{item}}</label>
            </div>
            <p class="form-text mb-1">{{description}}</p>
          </div>
        </div>`,
        popoverTemplate:
        `<form>
          <div class="form-group mb-2">
            <label class="control-label">{{nameLabel}}</label>
            <input type="text" ng-model="label" class="form-control"/>
          </div>
          <div class="form-group mb-2">
            <label class="control-label">{{descriptionLabel}}</label>
            <input type="text" ng-model="description" class="form-control"/>
          </div>
          <div class="form-group mb-2">
            <label class="control-label">{{optionsLabel}}</label>
            <textarea class="form-control" rows="3" ng-model="optionsText"/>
          </div>
          <div class="form-group mb-2">
            <label class="control-label">{{analysisLabel}}</label>
            <select ng-model="analysis" ng-options="obj.value as obj.option for obj in getAnalysisOptions('checkbox', null)" class="form-control custom-select"></select>
          </div>
          <div class="form-group mb-2 mt-4 text-right">
            <input type="button" ng-click="popover.remove($event)" class="btn btn-danger mr-1" value="{{deleteLabel}}"/>
            <input type="button" ng-click="popover.cancel($event)" class="btn btn-secondary mr-1" value="{{cancelLabel}}"/>
            <input type="submit" ng-click="popover.save($event)" class="btn btn-primary" value="{{saveLabel}}"/>
          </div>
        </form>`
      });

      $builderProvider.registerComponent("textarea", {
        group: "Default",
        label: "Comment",
        description: i18n.gettext("Comment Question"),
        placeholder: "",
        required: false,
        template:
        `<div class="form-group row">
          <label for="{{label}}" class="col-3 control-label text-right mt-1" ng-class="{'fb-required':required}">{{label}}</label>
          <div class="col-8">
            <textarea ng-model="inputText" rows="1" validator-required="{{required}}" validator-group="{{formName}}" id="{{label}}" class="form-control" placeholder="{{placeholder}}"></textarea>
            <p class="form-text mb-1">{{description}}</p>
          </div>
        </div>`,
        popoverTemplate:
        `<form>
          <div class="form-group mb-2">
            <label class="control-label">{{nameLabel}}</label>
            <input type="text" ng-model="label" class="form-control"/>
          </div>
          <div class="form-group mb-2">
            <label class="control-label">{{descriptionLabel}}</label>
            <input type="text" ng-model="description" class="form-control"/>
          </div>
          <div class="form-group mb-2">
            <label class="control-label">{{analysisLabel}}</label>
            <select ng-model="analysis" ng-options="obj.value as obj.option for obj in getAnalysisOptions('textarea', null)" class="form-control custom-select"></select>
          </div>
          <div class="form-group mb-2" ng-if="validationOptions.length > 0">
            <label class="control-label">{{validationLabel}}</label>
            <select ng-model="$parent.validation" class="form-control custom-select" ng-options="option.rule as option.label for option in validationOptions"></select>
          </div>
          <div class="form-group mb-2 mt-4 text-right">
            <input type="button" ng-click="popover.remove($event)" class="btn btn-danger mr-1" value="{{deleteLabel}}"/>
            <input type="button" ng-click="popover.cancel($event)" class="btn btn-secondary mr-1" value="{{cancelLabel}}"/>
            <input type="submit" ng-click="popover.save($event)" class="btn btn-primary" value="{{saveLabel}}"/>
          </div>
        </form>`
      });

      return $builderProvider.registerComponent("image", {
        group: "Default",
        label: "Image",
        description: i18n.gettext("Image Attachment"),
        placeholder: "",
        required: false,
        template:
        `<div class="form-group row">
          <label for="{{label}}" class="col-3 control-label text-right mt-1" ng-class="{'fb-required':required}">{{label}}</label>
          <div class="col-8">
            <div class="alert alert-dark"><i class="fa fa-image"></i> ${i18n.gettext('Image')}</div>
            <p class="form-text mb-1">{{description}}</p>
          </div>
        </div>`,
        popoverTemplate:
        `<form>
          <div class="form-group mb-2">
            <label class="control-label">{{nameLabel}}</label>
            <input type="text" ng-model="label" class="form-control"/>
          </div>
          <div class="form-group mb-2">
            <label class="control-label">{{descriptionLabel}}</label>
            <input type="text" ng-model="description" class="form-control"/>
          </div>
          <div class="form-group mb-2">
            <label class="control-label">{{analysisLabel}}</label>
            <select ng-model="analysis" ng-options="obj.value as obj.option for obj in getAnalysisOptions('textarea', null)" class="form-control custom-select"></select>
          </div>
          <div class="form-group mb-2" ng-if="validationOptions.length > 0">
            <label class="control-label">{{validationLabel}}</label>
            <select ng-model="$parent.validation" class="form-control custom-select" ng-options="option.rule as option.label for option in validationOptions"></select>
          </div>
          <div class="form-group mb-2 mt-4 text-right">
            <input type="button" ng-click="popover.remove($event)" class="btn btn-danger mr-1" value="{{deleteLabel}}"/>
            <input type="button" ng-click="popover.cancel($event)" class="btn btn-secondary mr-1" value="{{cancelLabel}}"/>
            <input type="submit" ng-click="popover.save($event)" class="btn btn-primary" value="{{saveLabel}}"/>
          </div>
        </form>`
      });
    }
  ]);
}).call(this);
