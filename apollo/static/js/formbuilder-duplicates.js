let getQuestionCodes = (builder) => {
  return builder.forms.default.filter(item => item.component !== 'group').map(item => item.label.toUpperCase());
};

let getSectionLabels = (builder) => {
  return builder.forms.default.filter(item => item.component === 'group').map(item => item.label.toUpperCase());
};


let makeCounter = (items) => {
  return items.reduce((accumulator, currentItem) => {
    accumulator[currentItem] = (accumulator[currentItem] || 0) + 1;
    return accumulator;
  }, {});
};

let getDuplicatedItems = (counter) => {
  let collector = [];
  for (const [item, count] of Object.entries(counter)) {
    if (count > 1)
      collector.push(item);
  }

  return collector;
};

let renderErrors = (duplicateCodes, duplicateSections) => {
  let getCodeErrorElement = () => {
    const codeMessage = i18n.ngettext(
      'The question code <strong>%2</strong> has been used more than once',
      'The question codes <strong>%2</strong> have been used more than once',
      duplicateCodes.length,
      duplicateCodes.join(', ')
    );

    let codeFragment = document.getElementById('errorCodes').content.cloneNode(true);
    codeFragment.firstElementChild.firstElementChild.innerHTML = codeMessage;

    return codeFragment;
  };
  let getSectionErrorElement = () => {
    const sectionMessage = i18n.ngettext(
      'The section <strong>%2</strong> has been used more than once',
      'The sections <strong>%2</strong> have been used more than once',
      duplicateSections.length,
      duplicateSections.join(', ')
    );;

    let sectionFragment = document.getElementById('errorSections').content.cloneNode(true);
    sectionFragment.firstElementChild.firstElementChild.innerHTML = sectionMessage;

    return sectionFragment;
  };

  let element = document.getElementById('errorContainer');
  if (duplicateCodes.length > 0 && duplicateSections.length > 0) {
    element.innerHTML = '';
    element.appendChild(getCodeErrorElement());
    element.appendChild(getSectionErrorElement());
  } else if (duplicateCodes.length > 0) {
    element.innerHTML = '';
    element.appendChild(getCodeErrorElement());
  } else if (duplicateSections.length > 0) {
    element.innerHTML = '';
    element.appendChild(getSectionErrorElement());
  }
};

let isFormStructureOk = (builder) => {
  // check for duplicated codes/section headers
  let duplicateCodes = getDuplicatedItems(makeCounter(getQuestionCodes(builder)));
  let duplicateSections = getDuplicatedItems(makeCounter(getSectionLabels(builder)));

  const flag = (duplicateCodes.length > 0) || (duplicateSections.length > 0);
  if (flag) {
    renderErrors(duplicateCodes, duplicateSections);
  }

  return !flag;
};