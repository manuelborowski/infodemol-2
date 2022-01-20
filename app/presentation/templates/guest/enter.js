$(document).ready(function () {
        const formOptions = {
        sanitizeConfig: {
            addTags: ['iframe'],
            addAttr: ['allow'],
            ALLOWED_TAGS: ['iframe'],
            ALLOWED_ATTR: ['allow']
        },
    }
    Formio.createForm(document.getElementById('register-form'), registration_form, formOptions).then(() => {
        console.log('form created')
    });
});



