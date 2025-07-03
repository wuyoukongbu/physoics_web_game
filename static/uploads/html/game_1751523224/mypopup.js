"use strict"

function createPopUps()
{
    let buttonHalfWidth = 100;
    let buttonFullWidth = 205;
    let buttonHeight = 35;
    

    helpButtons = [
        new Button({
            position: new p5.Vector((innerWidth / 2) + (buttonHalfWidth / 4), (innerHeight / 2) + 150), 
            width: buttonHalfWidth, 
            height: buttonHeight, 
            text: "Next", 
            onClick: function(){ currentPopUp++ }
        }),
        new Button({
            position: new p5.Vector((innerWidth / 2) - (buttonHalfWidth), (innerHeight / 2) + 150), 
            width: buttonHalfWidth, 
            height: buttonHeight, 
            text: "Previous", 
            onClick: function(){ currentPopUp-- }
        }),
        new Button({
            position: new p5.Vector((innerWidth / 2) + 160, (innerHeight / 2) - 180), 
            width: 30, 
            height: 30, 
            text: "×", 
            onClick: function(){ showHelp = false }
        })
    ]

    helpText = [
        "Double click anywhere to create a charge.",
        "The slider underneath the charge can be used to adjust the magnitude and sign of that charge.",
        "Charges can also be dragged around the screen by clicking and dragging on them.",
        "Drag a charge to the trash icon to delete it",
        "The checkboxes on the right side of the screen can be used to toggle the different features in the simulation.",
    ]
}

function displayPopUp()
{
    if (showHelp)
    {
        if (currentPopUp == 0)
        {
            helpButtons[1].visible = false
        }
        else 
        {
            helpButtons[1].visible = true
        }

        if (currentPopUp == 4)
        {
            helpButtons[0].visible = false
        }
        else 
        {
            helpButtons[0].visible = true
        }
        
        let canvas = foreGroundCanvas;
        canvas.push();
            canvas.noStroke();
            canvas.fill("rgba(0, 0, 0, 0.75)");
            canvas.rect(0, 0, innerWidth, innerHeight);
    
            canvas.fill(255);
            canvas.rect((innerWidth / 2) - 200, (innerHeight / 2) - 200, 400, 400);

            let scale = 0.25

            if (currentPopUp == 0)
            {
                canvas.image(helpImages[currentPopUp], (innerWidth / 2) - ((1559 * scale) / 2), (innerHeight / 2) - ((692 * scale) / 2) - 50, 1559 * scale, 692 * scale);
            }
            if (currentPopUp == 1)
            {
                canvas.image(helpImages[currentPopUp], (innerWidth / 2) - ((1559 * scale) / 2), (innerHeight / 2) - ((731 * scale) / 2) - 50, 1559 * scale, 731 * scale);
            }
            if (currentPopUp == 2)
            {
                scale = 0.17
                canvas.image(helpImages[currentPopUp], (innerWidth / 2) - ((1560 * scale) / 2), (innerHeight / 2) - ((1012 * scale) / 2) - 50, 1560 * scale, 1012 * scale);
            }
            if (currentPopUp == 3)
            {
                scale = 0.15
                canvas.image(helpImages[currentPopUp], (innerWidth / 2) - ((1560 * scale) / 2), (innerHeight / 2) - ((1262 * scale) / 2) - 50, 1560 * scale, 1262 * scale);
            }
            if (currentPopUp == 4)
            {
                scale = 0.06
                canvas.image(helpImages[currentPopUp], (innerWidth / 2) - ((1560 * scale) / 2), (innerHeight / 2) - ((3150 * scale) / 2) - 50, 1560 * scale, 3150 * scale);
            }
                canvas.fill(0)
                canvas.textSize(18)
                canvas.textAlign(canvas.CENTER)
                canvas.text(helpText[currentPopUp], (innerWidth / 2) - 200, (innerHeight / 2) + 50, 400, 200)
            // }
    
        canvas.pop();

        helpButtons.forEach(button => {
            if (button.visible)
            {
                button.display()
            }
        })
    }
    
}