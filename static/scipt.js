
document.getElementById('login-form').addEventListener('submit', function(e) {
  e.preventDefault();

  // Get email and password values
  const email = document.getElementById('email').value;
  const password = document.getElementById('password').value;

  // Check if fields are not empty
  if (email && password) {
    alert('Login successful!');
    // You can add further logic here, such as sending the data to the backend
  } else {
    alert('Please fill in all fields');
  }
});
