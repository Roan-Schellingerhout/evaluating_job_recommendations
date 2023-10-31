// Get the checkboxes and the target div
const checkbox = document.querySelector('#graph2c');
const childDiv = document.querySelector('.child2');

// Add event listeners to the checkboxes
checkbox2.addEventListener('change', updateMargin);

// Function to update the margin
function updateMargin() {
  // Check if at least one checkbox is checked
  if (checkbox.checked) && (screen.width <= 1080) {
    // Add the margin-top property to the child div
    console.log("adding margin")
    childDiv.style.marginTop = '25em';
  } else {
    // Remove the margin-top property from the child div
    childDiv.style.marginTop = '';
  }
}