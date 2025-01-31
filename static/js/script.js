// Detect request animation frame
const scroll =
  window.requestAnimationFrame ||
  // IE Fallback
  function (callback) {
    window.setTimeout(callback, 1000 / 60);
  };
const elementsToShow = document.querySelectorAll(".show-on-scroll");

function loop() {
  elementsToShow.forEach(function (element) {
    if (isElementInViewport(element)) {
      element.classList.add("is-visible");
    } else {
      element.classList.remove("is-visible");
    }
  });

  scroll(loop);
}

// Call the loop for the first time
loop();
function isElementInViewport(el) {
  // special bonus for those using jQuery
  if (typeof jQuery === "function" && el instanceof jQuery) {
    el = el[0];
  }
  const rect = el.getBoundingClientRect();
  return (
    (rect.top <= 0 && rect.bottom >= 0) ||
    (rect.bottom >=
      (window.innerHeight || document.documentElement.clientHeight) &&
      rect.top <=
        (window.innerHeight || document.documentElement.clientHeight)) ||
    (rect.top >= 0 &&
      rect.bottom <=
        (window.innerHeight || document.documentElement.clientHeight))
  );
}

// Smooth scroll function
const headerBtn = document.getElementById("header-btn");
const socialContact = document.getElementById("social-contact");
const contactForm = document.getElementById("contact");

function scrollToForm() {
  contactForm.scrollIntoView({ behavior: "smooth" }); // Top
}

headerBtn.addEventListener("click", scrollToForm);
socialContact.addEventListener("click", scrollToForm);

// No bots!
const contactFormNoBots = document.getElementById("contact-form-no-bots");
contactFormNoBots.parentNode.removeChild(contactFormNoBots);

function switchProfileImage() {
  const image1 = document.getElementById('image1');
  const image2 = document.getElementById('image2');

  // Define the image URLs
  const images = [
    "/static/images/profile_pic.jpg",  // First image
    "/static/images/profile_pic_2.jpg" // Second image
  ];

  // Initial images setup
  image1.style.backgroundImage = `url(${images[0]})`; // Set the first image
  image2.style.backgroundImage = `url(${images[1]})`; // Set the second image

  // Set initial opacity for images
  image1.style.opacity = '1'; // Make the first image visible
  image2.style.opacity = '0'; // Make the second image hidden

  // Function to switch between images
  function switchImage() {
    if (image1.style.opacity === '1') {
      image1.style.opacity = '0';  // Hide image1
      image2.style.opacity = '1';  // Show image2
    } else {
      image1.style.opacity = '1';  // Show image1
      image2.style.opacity = '0';  // Hide image2
    }
  }

  // Add event listener for the chatbot button click to switch images
  const chatbotButton = document.getElementById('chatbot');
  if (chatbotButton) {
    chatbotButton.addEventListener('click', function() {
      switchImage(); // Switch images on button click
    });
  }
}

// Ensure the function runs only when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', function() {
  switchProfileImage(); // Call the function when DOM is ready
});



(function () {
  const projects = document.querySelectorAll(".project");
  const detailsText = document.getElementById("details-text"); // Project details in chatbot

  projects.forEach((project) => {
    let typingEffect;

    project.addEventListener("mouseover", () => {
      const details = project.getAttribute("data-details");
      detailsText.innerHTML = ""; // Clear existing text using innerHTML
      let i = 0;

      // Clear any previous typing effect
      clearInterval(typingEffect);

      // Start new typing effect
      typingEffect = setInterval(() => {
        if (i < details.length) {
          detailsText.innerHTML += details[i];
          i++;
          // Check if the text exceeds the container width
          if (detailsText.scrollHeight > detailsText.clientHeight) {
            detailsText.innerHTML += "<br/>"; // Add line break when text exceeds the container height
          }
        } else {
          clearInterval(typingEffect);
        }
      }, 20);
    });

    // Clear details when the mouse leaves
    project.addEventListener("mouseleave", () => {
      clearInterval(typingEffect);
      detailsText.innerHTML = ""; // Clear text on mouse leave
    });
  });
})();

(function () {
  document.addEventListener("DOMContentLoaded", function () {
    const form = document.querySelector(".contact-form");
    const submitButton = document.getElementById("contact-form-submit");

    if (form && submitButton) {
      form.addEventListener("submit", function (event) {
        event.preventDefault(); // Prevent default form submission behavior
        submitButton.textContent = "Sending..."; // Update button text to indicate submission

        const formData = new FormData(form);
        const actionUrl = form.action;

        // Submit the form data using Fetch API
        fetch(actionUrl, {
          method: "POST",
          body: formData,
        })
          .then((response) => {
            if (response.ok) {
              // Clear form fields
              form.reset();
              // Display success message
              alert("Message sent succesfully!");
            } else {
              // Display error message
              alert("Error: Could not send the message. Please try again.");
            }
          })
          .catch((error) => {
            // Handle fetch errors
            console.error("Error sending the message:", error);
            alert("An unexpected error occurred. Please try again.");
          })
          .finally(() => {
            // Reset button text
            submitButton.textContent = "Send Message";
          });
      });
    }
  });
})();

const floatingButton = document.getElementById("floating-button");
const menuOptions = document.getElementById("menu-options");
const chatbotContainer = document.getElementById("chatbot-container");
const downloadButton = document.getElementById("download");
const blogsButton = document.getElementById("blogs");
const closeChatbot = document.getElementById("close-chatbot");

// Toggle the menu when clicking the floating button
floatingButton.addEventListener("click", function (event) {
  event.stopPropagation(); // Prevent clicking from closing the menu immediately
  floatingButton.classList.toggle("active");

  if (floatingButton.classList.contains("active")) {
    menuOptions.style.display = "flex"; // Show menu options when button is active
  } else {
    menuOptions.style.display = "none"; // Hide menu options when button is not active
  }
});

// Close the menu if clicked outside of the floating button or menu
document.addEventListener("click", function (event) {
  if (!floatingButton.contains(event.target) && !menuOptions.contains(event.target)) {
    floatingButton.classList.remove("active");
    menuOptions.style.display = "none"; // Hide the menu when clicked outside
  }
});

// Prevent the menu from closing when clicking inside the menu
menuOptions.addEventListener("click", function (event) {
  event.stopPropagation(); // Prevent closing menu when clicking inside
});

// Handle the Chatbot Button click
document.getElementById("chatbot").addEventListener("click", function () {
  chatbotContainer.style.display = "flex"; // Show the chatbot container
  floatingButton.classList.remove("active");
  menuOptions.style.display = "none"; // Close menu after selection
});

// Handle the Download Button click
document.getElementById("download").addEventListener("click", function () {
  const pdfUrl = "static/files/Rohith_Resume.pdf"; // Specify the PDF file path
  const link = document.createElement("a");
  link.href = pdfUrl;
  link.download = "Rohith_Resume.pdf"; // Specify the name of the file to be downloaded
  link.click(); // Trigger the download action
  floatingButton.classList.remove("active"); // Optionally collapse the menu
  menuOptions.style.display = "none"; // Close menu after selection
});

// Handle the Blogs Button click
document.getElementById("blogs").addEventListener("click", function () {
  window.open("https://rohithn.site", "_blank"); // Replace with your actual blog link
  floatingButton.classList.remove("active"); // Optionally collapse the menu
  menuOptions.style.display = "none"; // Close menu after selection
});

// Close chatbot container
closeChatbot.addEventListener("click", function () {
  chatbotContainer.style.display = "none"; // Hide the chatbot container
});

// Select the input field and send button
const chatbotInput = document.getElementById("chatbot-input");
const sendChatbot = document.getElementById("send-chatbot");

function sendMessage() {
  const message = chatbotInput.value.trim();
  if (message) {
    // Display the user's message in the chatbot
    const messageElement = document.createElement("div");
    messageElement.textContent = message;
    messageElement.classList.add("user-message");
    document.querySelector(".chatbot-messages").appendChild(messageElement);

    // Clear the input field
    chatbotInput.value = "";

    // Add the typing indicator before bot response
    const typingIndicator = document.createElement("div");
    typingIndicator.classList.add("bot-message", "typing");
    typingIndicator.textContent = "Typing...";
    document.querySelector(".chatbot-messages").appendChild(typingIndicator);

    // Send the message to the Flask backend
    fetch("/send_message", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ message: message }),
    })
    .then(response => response.json())
    .then(data => {
      const botResponse = data.response;

      // Remove the typing indicator
      const typingMessage = document.querySelector(".typing");
      if (typingMessage) {
        typingMessage.remove();
      }

      // Display the AI response with typing effect (one word at a time)
      const botMessageElement = document.createElement("div");
      botMessageElement.classList.add("bot-message");

      // Split the response into words and simulate typing
      const words = botResponse.split(' ');
      let wordIndex = 0;

      // Function to simulate typing each word
      function typeWord() {
        if (wordIndex < words.length) {
          botMessageElement.textContent += words[wordIndex] + " "; // Add word
          wordIndex++;
          setTimeout(typeWord, 100); // Delay for typing effect (200ms per word)
        }
      }

      // Start the typing effect
      document.querySelector(".chatbot-messages").appendChild(botMessageElement);
      typeWord(); // Start typing the message
    })
    .catch(error => {
      console.error("Error:", error);
    });
  }
}

// Listen for Enter key press in the input field
chatbotInput.addEventListener("keydown", function (event) {
  if (event.key === "Enter") {
    event.preventDefault(); // Prevent form submission or new line
    event.stopPropagation(); // Ensure other JS doesn't get affected by this event
    sendMessage(); // Trigger message send on Enter
  }
});

// Listen for click on send button
sendChatbot.addEventListener("click", function(event) {
  event.stopPropagation(); // Ensure click event does not affect other JS
  sendMessage(); // Trigger message send on button click
});

// Function to initialize and update the scroll progress bar
function initializeScrollProgressBar() {
  // Select the progress bar element
  const progressBar = document.querySelector('.progress-bar');
  
  // Ensure that the progress bar exists in the DOM
  if (!progressBar) {
    console.error('Progress bar element not found!');
    return;
  }

  // Add scroll event listener
  window.addEventListener('scroll', function() {
    // Get the total scrollable height of the document
    let scrollHeight = document.documentElement.scrollHeight - window.innerHeight;
    
    // Get the current scroll position
    let scrollPosition = window.scrollY;
    
    // Calculate the scroll progress as a percentage
    let progress = (scrollPosition / scrollHeight) * 100;
    
    // Update the height of the progress bar (ensure the height is between 0 and 100%)
    progress = Math.min(100, Math.max(0, progress));
    
    // Update the height of the progress bar
    progressBar.style.height = progress + '%';
  });
}

// Call the function to initialize the scroll progress bar
initializeScrollProgressBar();
