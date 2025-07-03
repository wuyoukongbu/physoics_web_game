"use strict"

function displayFieldLines()
{
    fieldLines.forEach(fieldLine => {
        fieldLine.display();
    });

    fieldLineArrows.forEach(fieldLineArrow => {
        fieldLineArrow.display();
    });
}



function createFieldLines()
{
    let canvas = foreGroundCanvas;
    fieldLines = [];
    fieldLineArrows = []

    charges.forEach(charge => {

        let radius = chargeRadius / 2;
        let times = Math.abs(charge.charge) * fieldLinesPerCoulomb;
        let origin = charge.position;

        let point = canvas.createVector(radius,radius);
        for (let a = 0; a < times; a++)
        // for (let a = 0; a < 1; a++)
        {
            let startingPosition = canvas.createVector(point.x + origin.x, point.y + origin.y)
            getFieldLinePoints(startingPosition);

            point.rotate((2 * Math.PI) / times);
        }
        
    });
}


function myAngleBetween(v1, v2)
{
    let dy = v1.y - v2.y;
    let dx = v1.x - v2.x;
    let theta = Math.atan2(dy, dx); // range (-PI, PI]
    theta *= 180 / Math.PI; // rads to degs, range (-180, 180]

    if (theta < 0) theta = 360 + theta; // range [0, 360)
    return theta;
}


function getFieldLinePoints(startingPosition, numberOfLoops, listOfPoints)
{
    let minVectorSize = 3;
    let maxVectorSize = chargeRadius;
    let vectorMag;

    if (listOfPoints == undefined) // only true the first time this funciton runs
    {
        listOfPoints = [];
        numberOfLoops = 0; 
        vectorMag = chargeRadius;
    }
    else
    {
        // let previousPosition = listOfPoints[listOfPoints.length - 1];
        // let angleBetweenPoints =  Math.abs( startingPosition.angleBetween(previousPosition) ) * (180 / Math.PI) ;
        // let angleBetweenPoints =  Math.abs( startingPosition.heading() - previousPosition.heading())
        // let angleBetweenPoints =  Math.abs( myAngleBetween(startingPosition, previousPosition) );
        vectorMag = chargeRadius;
        // if (angleBetweenPoints > 5) 
        // {
        //     console.log("big");    
        //     vectorMag = 1;
        // }
        // console.log(angleBetweenPoints);

        // vectorMag = Math.round(maxVectorSize * Math.pow(2, angleBetweenPoints));
        

        // console.log(numberOfLoops);
        if (numberOfLoops < 10)
        {
            vectorMag = chargeRadius / 4;
        }

        if (startingPosition.x > innerWidth || 
            startingPosition.x < 0 || 
            startingPosition.y > innerHeight || 
            startingPosition.y < 0)
        {
            vectorMag = 50
        }

        if (startingPosition.x > innerWidth + 100 || 
            startingPosition.x < 0 - 100 || 
            startingPosition.y > innerHeight + 100 || 
            startingPosition.y < 0 - 100)
        {
            vectorMag = 100
        }

        if (startingPosition.x > innerWidth + 200 || 
            startingPosition.x < 0 - 200 || 
            startingPosition.y > innerHeight + 200 || 
            startingPosition.y < 0 - 200)
        {
            vectorMag = 200
        }

        // if (startingPosition.x > innerWidth + 500 || 
        //     startingPosition.x < 0 - 500 || 
        //     startingPosition.y > innerHeight + 500 || 
        //     startingPosition.y < 0 - 500)
        // {
        //     vectorMag = 500
        // }
        // vectorMag = 1000 / angleBetweenPoints ;

        // console.log(vectorMag);

        // if (vectorMag > maxVectorSize) vectorMag = maxVectorSize;
        // if (vectorMag < minVectorSize) vectorMag = minVectorSize;
    }

    listOfPoints.push(startingPosition);

    let forceVector = netForceAtPoint(startingPosition).setMag(vectorMag);
    if (noPositiveCharges) 
    {
        forceVector.mult(-1);
    }

    let forceVectorFinalPosition = p5.Vector.add(forceVector, startingPosition);

    if (numberOfLoops % 7 == 0 && numberOfLoops > 6) 
    {
        let arrowPosition = startingPosition;
        let arrowAngle = noPositiveCharges ? forceVector.mult(-1).heading() : forceVector.heading();

        fieldLineArrows.push(new FieldLineArrow(arrowPosition, arrowAngle));
    }

    let distanceToCharges = [];
    charges.forEach(charge => {
        let finalPositionToChargeDistance = p5.Vector.dist(startingPosition, charge.position);
        distanceToCharges.push(finalPositionToChargeDistance);
    })
    let closestChargeDistance = Math.min(...distanceToCharges)

    let index = distanceToCharges.indexOf(closestChargeDistance);

    if (closestChargeDistance > chargeRadius / 2 && numberOfLoops < 310) 
    {
        getFieldLinePoints(forceVectorFinalPosition, numberOfLoops + 1, listOfPoints);
    }
    else if (closestChargeDistance < chargeRadius / 2 && charges[index].charge == 0)
    {
        getFieldLinePoints(forceVectorFinalPosition, numberOfLoops + 1, listOfPoints);
    }
    else if (closestChargeDistance < chargeRadius / 2 && charges[index].charge != 0)
    {
        listOfPoints.push(charges[index].position);
        fieldLines.push(new FieldLine(listOfPoints));
    }
    else
    {
        fieldLines.push(new FieldLine(listOfPoints));
    }
}



class FieldLine
{
    constructor(fieldLinePoints)
    {
        this.fieldLinePoints = fieldLinePoints;
    }
    
    display()
    {
        let canvas = foreGroundCanvas;
        canvas.beginShape();
        // canvas.beginShape(canvas.POINTS);
        canvas.noFill();
            canvas.stroke(255);
            canvas.vertex(this.fieldLinePoints[0].x, this.fieldLinePoints[0].y)
            this.fieldLinePoints.forEach(point => {
                canvas.curveVertex(point.x, point.y);
            })
        canvas.endShape();


        // // let canvas = foreGroundCanvas;
        // // canvas.beginShape();
        // canvas.strokeWeight(5)
        // canvas.beginShape(canvas.POINTS);
        // canvas.noFill();
        //     canvas.stroke(255);
        //     canvas.vertex(this.fieldLinePoints[0].x, this.fieldLinePoints[0].y)
        //     this.fieldLinePoints.forEach(point => {
        //         canvas.curveVertex(point.x, point.y);
        //     })
        // canvas.endShape();
        // canvas.strokeWeight(1)

        
    }
}



class FieldLineArrow
{
    constructor(position, direction)
    {
        this.position = position;
        this.direction = direction;
    }

    display()
    {
        let canvas = foreGroundCanvas;
        canvas.push();
            canvas.stroke(255);
            canvas.translate(this.position.x, this.position.y)
            canvas.rotate(this.direction);
            canvas.fill(255);
            canvas.triangle(0, 0, -10, -5, -10, 5);
        canvas.pop();
    }
}