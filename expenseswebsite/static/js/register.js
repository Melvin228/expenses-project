const usernameField = document.querySelector("#usernameField");
const feedbackField = document.querySelector(".invalid-feedback");
const emailField = document.querySelector("#emailField");
const emailFeedbackField = document.querySelector(".email-feedback");
const usernameSuccessOutput = document.querySelector(".usernameSuccessOutput");
const showPasswordToggle = document.querySelector(".showPasswordToggle");
const passwordField = document.querySelector("#passwordField");
const submitBtn = document.querySelector(".submit-btn");

//for username

usernameField.addEventListener("keyup", (e) => {
  const usernameVal = e.target.value;

  usernameField.classList.remove("is-invalid");
  feedbackField.style.display = "none";

  usernameSuccessOutput.style.display = "block";

  if (usernameVal.length > 0) {
    // usernameSuccessOutput.textContent = `Checking ${usernameVal}`;
    fetch("/authentication/validate-username", {
      body: JSON.stringify({ username: usernameVal }),
      method: "POST",
    })
      .then((response) => response.json())
      .then((data) => {
        usernameSuccessOutput.style.display = "none";
        if (data.username_error) {
          submitBtn.disabled = true;
          usernameField.classList.add("is-invalid");
          feedbackField.style.display = "block";
          feedbackField.innerHTML = `<p>${data.username_error}</p>`;
        } else {
          submitBtn.removeAttribute("disabled");
        }
      });
  }
});

//for email

emailField.addEventListener("keyup", (e) => {
  const emailVal = e.target.value;

  emailField.classList.remove("is-invalid");
  emailFeedbackField.style.display = "none";

  if (emailVal.length > 0) {
    fetch("/authentication/validate-email", {
      body: JSON.stringify({ email: emailVal }),
      method: "POST",
    })
      .then((res) => res.json())
      .then((data) => {
        if (data.email_error) {
          submitBtn.disabled = true;
          emailField.classList.add("is-invalid");
          emailFeedbackField.style.display = "block";
          emailFeedbackField.innerHTML = `<p>${data.email_error}</p>`;
        } else {
          submitBtn.removeAttribute("disabled");
        }
      });
  }
});

const handleToggleInput = (e) => {
  if (showPasswordToggle.textContent === "SHOW") {
    showPasswordToggle.textContent = "HIDE";
    passwordField.setAttribute("type", "text");
  } else {
    showPasswordToggle.textContent = "SHOW";
    passwordField.setAttribute("type", "password");
  }
};

showPasswordToggle.addEventListener("click", handleToggleInput);
