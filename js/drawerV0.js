
// By Simon Sarris
// www.simonsarris.com
// sarris@acm.org
//
// Code from the following pages merged by Andrew Clark (amclark7@gmail.com):
//   http://simonsarris.com/blog/510-making-html5-canvas-useful
//   http://simonsarris.com/blog/225-canvas-selecting-resizing-shape
// Last update June 2013
//
// Free to use and distribute at will
// So long as you are nice to people, etc

// Constructor for Shape objects to hold data for all drawn objects.
// For now they will just be defined as rectangles.
var width = 5;
var height = 10;
var INTERSPACE = 1.5;
var MOVING_CONSTANTX = 7.5;
var MOVING_CONSTANTY = 12.5;
var LEFTSPACE = 5;
var resourcesType = ["LAB", "DSP", "MK20"];
var DEFAULTIMELIMIT = 18;
var DEFAULTGENMODE = "irreducible";
var s;
var objectiveFunction;
var topScrollPosition = 0;
var leftScrollPosition = 0;


function colour(type) {
    switch (type) {
        case 'DSP':
            return 'OrangeRed';
        case 'LAB':
            return 'Lime';
        case 'MK20':
            return 'Yellow';
        case 'NonRec':
            return 'Silver';
    }
}

function ObjectiveFunction() {
    this.wirelength = 0;
    this.perimeter = 0;
    this.wastedResources = 0;
    this.bitstream = 0;
    this.genMode = DEFAULTGENMODE;
    this.timeLimit = DEFAULTIMELIMIT;
    this.precision = "low";
}

ObjectiveFunction.prototype.updateWire = function (newValue) {
    this.wirelength = newValue;
};

ObjectiveFunction.prototype.updatePerimeter = function (newValue) {
    this.perimeter = newValue;
};

ObjectiveFunction.prototype.updateWasted = function (newValue) {
    this.wastedResources = newValue;
};

ObjectiveFunction.prototype.updateBitstream = function (newValue) {
    this.bitstream = newValue;
};


function Shape(state, x, y, w, h, fill, id) {
    "use strict";
    // This is a very simple and unsafe constructor. All we're doing is checking if the values exist.
    // "x || 0" just means "if there is a value for x, use that. Otherwise use 0."
    // But we aren't checking anything else! We could put "Lalala" for the value of x 
    this.state = state;
    this.x = x || 0;
    this.y = y || 0;
    this.w = w || 1;
    this.h = h || 1;
    this.row = 0;
    this.column = 0;
    this.width = 3;
    this.height = 3;
    this.id = id;
    this.fill = fill || '#AAAAAA';
    this.coveredDsp = 0;
    this.coveredLab = 0;
    this.coveredMK20 = 0;
    this.requiredDsp = 0;
    this.requiredLab = 0;
    this.requiredMK20 = 0;
}

// Draws this shape to a given context
Shape.prototype.draw = function (ctx, optionalColor) {
    var i, cur, half;
    ctx.fillStyle = this.fill;
    ctx.fillRect(this.x, this.y, this.w, this.h);
    if (this.state.selection === this) {
        ctx.strokeStyle = this.state.selectionColor;
        ctx.lineWidth = this.state.selectionWidth;
        ctx.strokeRect(this.x, this.y, this.w, this.h);

        // draw the boxes
        half = this.state.selectionBoxSize / 2;

        // 0  1  2
        // 3     4
        // 5  6  7

        // top left, middle, right
        this.state.selectionHandles[0].x = this.x - half;
        this.state.selectionHandles[0].y = this.y - half;

        this.state.selectionHandles[1].x = this.x + this.w / 2 - half;
        this.state.selectionHandles[1].y = this.y - half;

        this.state.selectionHandles[2].x = this.x + this.w - half;
        this.state.selectionHandles[2].y = this.y - half;

        //middle left
        this.state.selectionHandles[3].x = this.x - half;
        this.state.selectionHandles[3].y = this.y + this.h / 2 - half;

        //middle right
        this.state.selectionHandles[4].x = this.x + this.w - half;
        this.state.selectionHandles[4].y = this.y + this.h / 2 - half;

        //bottom left, middle, right
        this.state.selectionHandles[6].x = this.x + this.w / 2 - half;
        this.state.selectionHandles[6].y = this.y + this.h - half;

        this.state.selectionHandles[5].x = this.x - half;
        this.state.selectionHandles[5].y = this.y + this.h - half;

        this.state.selectionHandles[7].x = this.x + this.w - half;
        this.state.selectionHandles[7].y = this.y + this.h - half;


        ctx.fillStyle = this.state.selectionBoxColor;
        for (i = 0; i < 8; i += 1) {
            cur = this.state.selectionHandles[i];
            ctx.fillRect(cur.x, cur.y, this.state.selectionBoxSize, this.state.selectionBoxSize);
        }
    }
};

// Determine if a point is inside the shape's bounds
Shape.prototype.contains = function (mx, my) {
    "use strict";
    // All we have to do is make sure the Mouse X,Y fall in the area between
    // the shape's X and (X + Height) and its Y and (Y + Height)

    return  (this.x - leftScrollPosition <= mx) && (this.x + this.w - leftScrollPosition >= mx) &&
            (this.y - topScrollPosition <= my) && (this.y + this.h - topScrollPosition >= my);
};

function Resource(row, column, type) {
    this.row = row;
    this.column = column;
    this.type = type;
}

Resource.prototype.draw = function (ctx) {
    var startingx = this.column + INTERSPACE * this.column + this.column * width + LEFTSPACE;
    var startingy = this.row + INTERSPACE * this.row + this.row * height + LEFTSPACE;
    ctx.fillStyle = colour(this.type);
    ctx.fillRect(startingx, startingy, width, height);
}

Shape.prototype.containsRsc = function (row, column) {

    return (this.row <= row) && (this.row + this.height > row) &&
            (this.column <= column) && (this.column + this.width > column);


}

function CanvasState(canvas) {
    "use strict";
    // **** First some setup! ****

    this.canvas = canvas;
    this.width = canvas.width;
    this.height = canvas.height;
    this.ctx = canvas.getContext('2d');
    // This complicates things a little but but fixes mouse co-ordinate problems
    // when there's a border or padding. See getMouse for more detail
    var stylePaddingLeft, stylePaddingTop, styleBorderLeft, styleBorderTop,
            html, myState, i;
    if (document.defaultView && document.defaultView.getComputedStyle) {
        this.stylePaddingLeft = parseInt(document.defaultView.getComputedStyle(canvas, null).paddingLeft, 10) || 0;
        this.stylePaddingTop = parseInt(document.defaultView.getComputedStyle(canvas, null).paddingTop, 10) || 0;
        this.styleBorderLeft = parseInt(document.defaultView.getComputedStyle(canvas, null).borderLeftWidth, 10) || 0;
        this.styleBorderTop = parseInt(document.defaultView.getComputedStyle(canvas, null).borderTopWidth, 10) || 0;
    }
    // Some pages have fixed-position bars (like the stumbleupon bar) at the top or left of the page
    // They will mess up mouse coordinates and this fixes that
    html = document.body.parentNode;
    this.htmlTop = html.offsetTop;
    this.htmlLeft = html.offsetLeft;

    // **** Keep track of state! ****

    this.valid = false; // when set to false, the canvas will redraw everything
    this.shapes = [];  // the collection of things to be drawn
    this.resources = [];
    this.dragging = false; // Keep track of when we are dragging
    this.resizeDragging = false; // Keep track of resize
    this.expectResize = -1; // save the # of the selection handle 
    // the current selected object. In the future we could turn this into an array for multiple selection
    this.selection = null;
    this.dragoffx = 0; // See mousedown and mousemove events for explanation
    this.dragoffy = 0;

    // New, holds the 8 tiny boxes that will be our selection handles
    // the selection handles will be in this order:
    // 0  1  2
    // 3     4
    // 5  6  7
    this.selectionHandles = [];
    for (i = 0; i < 8; i += 1) {
        this.selectionHandles.push(new Shape(this));
    }

    // **** Then events! ****

    // This is an example of a closure!
    // Right here "this" means the CanvasState. But we are making events on the Canvas itself,
    // and when the events are fired on the canvas the variable "this" is going to mean the canvas!
    // Since we still want to use this particular CanvasState in the events we have to save a reference to it.
    // This is our reference!
    myState = this;

    //fixes a problem where double clicking causes text to get selected on the canvas
    canvas.addEventListener('selectstart', function (e) {
        e.preventDefault();
        return false;
    }, false);
    // Up, down, and move are for dragging
    canvas.addEventListener('mousedown', function (e) {
        var mouse, mx, my, shapes, l, i, mySel;
        if (myState.expectResize !== -1) {
            myState.resizeDragging = true;
            return;
        }
        mouse = myState.getMouse(e);
        mx = mouse.x;
        my = mouse.y;
        shapes = myState.shapes;
        l = shapes.length;
        for (i = l - 1; i >= 0; i -= 1) {
            if (shapes[i].contains(mx, my)) {
                mySel = shapes[i];
                // Keep track of where in the object we clicked
                // so we can move it smoothly (see mousemove)
                myState.dragoffx = mx - mySel.x;
                myState.dragoffy = my - mySel.y;
                myState.dragging = true;
                myState.selection = mySel;
                myState.valid = false;
                return;
            }
        }
        // havent returned means we have failed to select anything.
        // If there was an object selected, we deselect it
        if (myState.selection) {
            myState.selection = null;
            myState.valid = false; // Need to clear the old selection border
        }
    }, true);
    canvas.addEventListener('mousemove', function (e) {
        var mouse = myState.getMouse(e),
                mx = mouse.x,
                my = mouse.y,
                oldx, oldy, i, cur;
        if (myState.dragging) {
            mouse = myState.getMouse(e);
            // We don't want to drag the object by its top-left corner, we want to drag it
            // from where we clicked. Thats why we saved the offset and use it here
            if (myState.selection.x - leftScrollPosition - mouse.x < 0) {
                myState.selection.x = myState.selection.x + MOVING_CONSTANTX;
                myState.selection.column = myState.selection.column + 1;
            }
            if (myState.selection.x - leftScrollPosition - mouse.x > 0) {
                myState.selection.x = myState.selection.x - MOVING_CONSTANTX;
                myState.selection.column = myState.selection.column - 1;
            }
            if (myState.selection.y - topScrollPosition - mouse.y < 0) {
                myState.selection.y = myState.selection.y + MOVING_CONSTANTY;

                myState.selection.row = myState.selection.row + 1;
            }
            if (myState.selection.y - topScrollPosition - mouse.y > 0) {
                myState.selection.y = myState.selection.y - MOVING_CONSTANTY;

                myState.selection.row = myState.selection.row - 1;
            }
            myState.valid = false;
            myState.valid = false; // Something's dragging so we must redraw
        } else if (myState.resizeDragging) {
            // time ro resize!
            oldx = myState.selection.x;
            oldy = myState.selection.y;

            // 0  1  2
            // 3     4
            // 5  6  7
            switch (myState.expectResize) {
                case 0:
                    if (oldx - mx - leftScrollPosition > 0 && oldy - my - topScrollPosition > 0) {
                        myState.selection.x = oldx - MOVING_CONSTANTX;
                        myState.selection.y = oldy - MOVING_CONSTANTY;
                        myState.selection.w += MOVING_CONSTANTX;
                        myState.selection.h += MOVING_CONSTANTY;
                        myState.selection.row = myState.selection.row - 1;
                        myState.selection.column = myState.selection.column - 1;
                        myState.selection.width = myState.selection.width + 1;
                        myState.selection.height = myState.selection.height + 1;
                    }
                    if (oldx - mx - leftScrollPosition < -MOVING_CONSTANTX && oldy - my - topScrollPosition < -MOVING_CONSTANTY) {
                        myState.selection.x = oldx + MOVING_CONSTANTX;
                        myState.selection.y = oldy + MOVING_CONSTANTY;
                        myState.selection.w -= MOVING_CONSTANTX;
                        myState.selection.h -= MOVING_CONSTANTY;
                        myState.selection.row = myState.selection.row + 1;
                        myState.selection.column = myState.selection.column + 1;
                        myState.selection.width = myState.selection.width - 1;
                        myState.selection.height = myState.selection.height - 1;
                    }
                    break;
                case 1:
                    if (oldy - my - topScrollPosition > 0) {
                        myState.selection.y = oldy - MOVING_CONSTANTY;
                        myState.selection.h += MOVING_CONSTANTY;
                        myState.selection.row = myState.selection.row - 1;
                        myState.selection.height = myState.selection.height + 1;
                    }
                    if (oldy - my - topScrollPosition < -MOVING_CONSTANTY) {
                        myState.selection.y = oldy + MOVING_CONSTANTY;
                        myState.selection.h -= MOVING_CONSTANTY;
                        myState.selection.row = myState.selection.row + 1;
                        myState.selection.height = myState.selection.height - 1;
                    }
                    break;
                case 2:
                    if (oldx - mx - leftScrollPosition < 0 && oldy - my - topScrollPosition > 0) {
                        myState.selection.y = oldy - MOVING_CONSTANTY;
                        myState.selection.w += MOVING_CONSTANTX;
                        myState.selection.h += MOVING_CONSTANTY;
                        myState.selection.row = myState.selection.row - 1;
                        myState.selection.column = myState.selection.column + 1;
                        myState.selection.width = myState.selection.width + 1;
                        myState.selection.height = myState.selection.height + 1;
                    }
                    if (oldy - my - topScrollPosition < -MOVING_CONSTANTY) {
                        myState.selection.y = oldy + MOVING_CONSTANTY;
                        myState.selection.w -= MOVING_CONSTANTX;
                        myState.selection.h -= MOVING_CONSTANTY;
                        myState.selection.row = myState.selection.row + 1;
                        myState.selection.column = myState.selection.column - 1;
                        myState.selection.width = myState.selection.width - 1;
                        myState.selection.height = myState.selection.height - 1;
                    }
                    break;
                case 3:
                    if (oldx - mx - leftScrollPosition > 0) {
                        myState.selection.x = oldx - MOVING_CONSTANTX;
                        myState.selection.w += MOVING_CONSTANTX;
                        myState.selection.column = myState.selection.column - 1;
                        myState.selection.width = myState.selection.width + 1;
                    }
                    if (oldx - mx - leftScrollPosition < -MOVING_CONSTANTX) {
                        myState.selection.x = oldx + MOVING_CONSTANTX;
                        myState.selection.w -= MOVING_CONSTANTX;
                        myState.selection.column = myState.selection.column + 1;
                        myState.selection.width = myState.selection.width - 1;
                    }
                    break;
                case 4:
                    if (oldx + myState.selection.w - mx - leftScrollPosition < 0) {
                        myState.selection.w += MOVING_CONSTANTX;
                        myState.selection.width = myState.selection.width + 1;
                    }
                    if (oldx + myState.selection.w - mx - leftScrollPosition > MOVING_CONSTANTX) {
                        myState.selection.w -= MOVING_CONSTANTX;
                        myState.selection.width = myState.selection.width - 1;
                    }
                    break;
                case 5:
                    if (oldx - mx - leftScrollPosition > 0 && oldy - my - topScrollPosition < 0) {
                        myState.selection.x = oldx - MOVING_CONSTANTX;
                        myState.selection.w += MOVING_CONSTANTX;
                        myState.selection.h += MOVING_CONSTANTY;
                        myState.selection.row = myState.selection.row - 1;
                        myState.selection.column = myState.selection.column + 1;
                        myState.selection.width = myState.selection.width + 1;
                        myState.selection.height = myState.selection.height + 1;
                    }
                    if (oldx - mx - leftScrollPosition < -MOVING_CONSTANTX) {
                        myState.selection.x = oldx + MOVING_CONSTANTX;
                        myState.selection.w -= MOVING_CONSTANTX;
                        myState.selection.h -= MOVING_CONSTANTY;
                        myState.selection.row = myState.selection.row + 1;
                        myState.selection.column = myState.selection.column - 1;
                        myState.selection.width = myState.selection.width - 1;
                        myState.selection.height = myState.selection.height - 1;
                    }
                    break;
                case 6:
                    if (oldy + myState.selection.h - my - topScrollPosition < 0) {
                        myState.selection.h += MOVING_CONSTANTY;
                        myState.selection.height = myState.selection.height + 1;
                    }
                    if (oldy + myState.selection.h - my - topScrollPosition > MOVING_CONSTANTY) {
                        myState.selection.h -= MOVING_CONSTANTY;
                        myState.selection.height = myState.selection.height - 1;

                    }

                    break;
                case 7:
                    if (oldx + myState.selection.w - mx - leftScrollPosition < 0 && oldy + myState.selection.h - my - topScrollPosition < 0) {
                        myState.selection.w += MOVING_CONSTANTX;
                        myState.selection.h += MOVING_CONSTANTY;
                        myState.selection.width = myState.selection.width + 1;
                        myState.selection.height = myState.selection.height + 1;
                    }
                    if (oldx + myState.selection.w - mx > MOVING_CONSTANTX && oldy + myState.selection.h - my > MOVING_CONSTANTY) {
                        myState.selection.w -= MOVING_CONSTANTX;
                        myState.selection.h -= MOVING_CONSTANTY;
                        myState.selection.width = myState.selection.width - 1;
                        myState.selection.height = myState.selection.height - 1;
                    }

                    break;
            }

            myState.valid = false; // Something's dragging so we must redraw
        }

        // if there's a selection see if we grabbed one of the selection handles
        if (myState.selection !== null && !myState.resizeDragging) {
            for (i = 0; i < 8; i += 1) {
                // 0  1  2
                // 3     4
                // 5  6  7

                cur = myState.selectionHandles[i];

                // we dont need to use the ghost context because
                // selection handles will always be rectangles
                if (mx >= cur.x - leftScrollPosition && mx <= cur.x - leftScrollPosition + myState.selectionBoxSize &&
                        my >= cur.y - topScrollPosition && my <= cur.y - topScrollPosition + myState.selectionBoxSize) {
                    // we found one!
                    myState.expectResize = i;
                    myState.valid = false;

                    switch (i) {
                        case 0:
                            this.style.cursor = 'nwse-resize';
                            break;
                        case 1:
                            this.style.cursor = 'ns-resize';
                            break;
                        case 2:
                            this.style.cursor = 'nesw-resize';
                            break;
                        case 3:
                            this.style.cursor = 'ew-resize';
                            break;
                        case 4:
                            this.style.cursor = 'ew-resize';
                            break;
                        case 5:
                            this.style.cursor = 'nesw-resize';
                            break;
                        case 6:
                            this.style.cursor = 'ns-resize';
                            break;
                        case 7:
                            this.style.cursor = 'nwse-resize';
                            break;
                    }
                    return;
                }

            }
            // not over a selection box, return to normal
            myState.resizeDragging = false;
            myState.expectResize = -1;
            this.style.cursor = 'auto';
        }
    }, true);
    canvas.addEventListener('mouseup', function (e) {
        myState.dragging = false;
        myState.resizeDragging = false;
        myState.expectResize = -1;
        if (myState.selection !== null) {
            if (myState.selection.w < 0) {
                myState.selection.w = -myState.selection.w;
                myState.selection.x -= myState.selection.w;
            }
            if (myState.selection.h < 0) {
                myState.selection.h = -myState.selection.h;
                myState.selection.y -= myState.selection.h;
            }
            updateCoverage(myState.selection);
        }
    }, true);

    // **** Options! ****

    this.selectionColor = '#CC0000';
    this.selectionWidth = 2;
    this.selectionBoxSize = 6;
    this.selectionBoxColor = 'darkred';
    this.interval = 5;
    setInterval(function () {
        myState.draw();
    }, myState.interval);
}

CanvasState.prototype.addShape = function (shape) {
    this.shapes.push(shape);
    this.valid = false;
};

CanvasState.prototype.addResource = function (resource) {
    this.resources.push(resource);
    this.valid = false;
};

CanvasState.prototype.clear = function () {
    this.ctx.clearRect(0, 0, this.width, this.height);
};

// While draw is called as often as the INTERVAL variable demands,
// It only ever does something if the canvas gets invalidated by our code
CanvasState.prototype.draw = function () {
    var ctx, shapes, i, shape, mySel;
    // if our state is invalid, redraw and validate!
    if (!this.valid) {
        ctx = this.ctx;
        shapes = this.shapes;
        var resources = this.resources;
        this.clear();

        // ** Add stuff you want drawn in the background all the time here **

        // draw all shapes
        var l = resources.length;
        for (var i = 0; i < l; i++) {
            resources[i].draw(ctx);
        }
        l = shapes.length;
        for (i = 0; i < l; i += 1) {
            shape = shapes[i];
            // We can skip the drawing of elements that have moved off the screen:
            //   if (shape.x <= this.width && shape.y <= this.height &&
            //            shape.x + shape.w >= 0 && shape.y + shape.h >= 0) {
            shapes[i].draw(ctx);
        }

        // draw selection
        // right now this is just a stroke along the edge of the selected Shape
        if (this.selection !== null) {
            ctx.strokeStyle = this.selectionColor;
            ctx.lineWidth = this.selectionWidth;
            mySel = this.selection;
            ctx.strokeRect(mySel.x, mySel.y, mySel.w, mySel.h);
        }

        // ** Add stuff you want drawn on top all the time here **

        this.valid = true;
    }
};


// Creates an object with x and y defined, set to the mouse position relative to the state's canvas
// If you wanna be super-correct this can be tricky, we have to worry about padding and borders
CanvasState.prototype.getMouse = function (e) {
    "use strict";
    var element = this.canvas, offsetX = 0, offsetY = 0, mx, my;

    // Compute the total offset
    if (element.offsetParent !== undefined) {
        do {
            offsetX += element.offsetLeft;
            offsetY += element.offsetTop;
            element = element.offsetParent;
        } while (element);
    }

    // Add padding and border style widths to offset
    // Also add the <html> offsets in case there's a position:fixed bar
    offsetX += this.stylePaddingLeft + this.styleBorderLeft + this.htmlLeft;
    offsetY += this.stylePaddingTop + this.styleBorderTop + this.htmlTop;

    mx = e.pageX - offsetX;
    my = e.pageY - offsetY;

    // We return a simple javascript object (a hash) with x and y defined
    return {x: mx, y: my};
};

// If you dont want to use <body onLoad='init()'>
// You could uncomment this init() reference and place the script reference inside the body tag
//init();

function addRegion() {
    var shape = new Shape(s, 4, 4, 22, 37, 'rgba(150,150,250,0.7)', s.shapes.length + 1);
    s.addShape(shape);
    updateView();
    updateCoverage(shape);
}

function updateView() {
    var htmlFields = '<p><b>Region ' + s.shapes.length + '</b></p>';
    htmlFields += '<table><tr><td>Required:</td>';



    for (var i = 0; i < resourcesType.length; i++)
        htmlFields += '<td>' + resourcesType[i] + ' <input onkeyup="updateValues();" onClick="justClick(this)" maxlength="4" onkeypress="return checkKey(event);" type="text" value="0" id="' + s.shapes.length + '_' + resourcesType[i] + '"></td>';

    htmlFields += '</tr><tr><td>Covered:</td>';

    for (var i = 0; i < resourcesType.length; i++) {
        htmlFields += '<td>' + resourcesType[i] + ' <input type="text" class="readonly" value="0" id="' + s.shapes.length + '_' + resourcesType[i] + '_r" readonly="readonly"></td>';
    }
    htmlFields += '</tr></table>';
    $("#regionInfo").append(htmlFields);


    // update stat fields
}

function checkKey(event) {
    return event.charCode >= 48 && event.charCode <= 57;
}

function justClick(element) {
    if (element.value === 0) {
        $(element.id).val(3);
    }
}

function updateCoverage(region) {
    var rscs = s.resources;
    region.coveredDsp = 0;
    region.coveredLab = 0;
    region.coveredMK20 = 0;
    for (var i = 0; i < rscs.length; i++) {
        if (region.containsRsc(rscs[i].row, rscs[i].column)) {
            updateCounter(region, rscs[i].type);
        }
    }
    updateCoverageView(region);

}

function updateValues() {
    for (var i = 0; i < s.shapes.length; i++) {
        var id1 = '#' + s.shapes[i].id + '_LAB';
        var id2 = '#' + s.shapes[i].id + '_DSP';
        var id3 = '#' + s.shapes[i].id + '_MK20';
        var required = $(id1).val();
        if (required !== '') {
            s.shapes[i].requiredLab = required;
        } else {
            s.shapes[i].requiredLab = 0;
        }
        required = $(id2).val();
        if (required !== '') {
            s.shapes[i].requiredDsp = required;
        } else {
            s.shapes[i].requiredDsp = 0;
        }
        required = $(id3).val();
        if (required !== '') {
            s.shapes[i].requiredMK20 = required;
        } else {
            s.shapes[i].requiredMK20 = 0;
        }
        s.shapes[i].requiredMK20 = $(id3).val();

    }
}

function updateCoverageView(region) {
    var id1 = '#' + region.id + '_LAB_r';
    var id2 = '#' + region.id + '_DSP_r';
    var id3 = '#' + region.id + '_MK20_r';
    $(id1).val(region.coveredLab);
    $(id2).val(region.coveredDsp);
    $(id3).val(region.coveredMK20);
}


function updateCounter(region, rscType) {
    switch (rscType) {
        case 'LAB':
            region.coveredLab++;
            break;
        case 'MK20':
            region.coveredMK20++;
            break;
        case 'DSP':
            region.coveredDsp++;
            break;
        default:
            break;
    }
}



function init(result) {
    var mydata = JSON.parse(result);
    var canvas = document.getElementById('my-canvas');
    canvas.width = (mydata.width) * (width + INTERSPACE + 1) + LEFTSPACE + 5;
    canvas.height = mydata.height * (height + INTERSPACE + 1) + LEFTSPACE;
    objectiveFunction = new ObjectiveFunction();
    s = new CanvasState(canvas);
    for (var i = 0; i < (mydata.width) * (mydata.height); i++) {
        var rsc = new Resource(mydata.blocks[i].y, mydata.blocks[i].x, mydata.blocks[i].t);
        s.addResource(rsc);
    }
    addRegion();
}




function ajaxmagic() {
    //   var menu = document.getElementById("fpgaSelection");
    $.ajax({
        type: "GET",
        url: "optimizationScript.php",
        data: "fpga=" + "aa", //menu.options[menu.selectedIndex].value,
        success: function (result) {
            init(result);
        }});
}

$(document).ready(function () {
    $("#drawDiv").scroll(function () {
        leftScrollPosition = $("#drawDiv").scrollLeft();
        topScrollPosition = $("#drawDiv").scrollTop();
    });


    $(function () {
        $("#sliderWL").slider({
            orientation: 'vertical',
            slide: function (evente, ui) {
                $("#qWL").val(ui.value);
                objectiveFunction.updateWire(ui.value);
            }

        });
    });





    $(function () {
        $("#sliderP").slider({
            orientation: 'vertical',
            slide: function (evente, ui) {
                $("#qP").val(ui.value);
                objectiveFunction.updatePerimeter(ui.value);
            }

        });
    });

    $(function () {
        $("#sliderBS").slider({
            orientation: 'vertical',
            slide: function (evente, ui) {
                $("#qBS").val(ui.value);
                objectiveFunction.updateBitstream(ui.value);
            }

        });
    });

    $(function () {
        $("#sliderR").slider({
            orientation: 'vertical',
            slide: function (evente, ui) {
                $("#qR").val(ui.value);
                objectiveFunction.updateWasted(ui.value);
            }

        });

    });

    $("input:radio[name=mode]").click(function () {
        objectiveFunction.genMode = $(this).val();
    });
});

function updateTime() {
    objectiveFunction.timeLimit = $("#TL").val();

}

function selectPrecision() {
    var menu = document.getElementById("precisionMenu");
    objectiveFunction.precision = menu.options[menu.selectedIndex].value;
    alert(objectiveFunction.precision);
}



function optimize() {
    
    $('#overlay').css('display','block');

    var toOpt = {};
    toOpt.regions_data = {};

    for (var i = 0; i < s.shapes.length; i++) {
        var item = "rec" + (i + 1);
        toOpt.regions_data[item] = {};
        toOpt.regions_data[item].resources = {};
        toOpt.regions_data[item].resources.LAB = s.shapes[i].requiredLab;
        toOpt.regions_data[item].resources.MK20 = s.shapes[i].requiredDsp;
        toOpt.regions_data[item].resources.DSP = s.shapes[i].requiredMK20;
    }

    toOpt.obj_weights = {};
    toOpt.obj_weights.wirelength = objectiveFunction.wirelength;
    toOpt.obj_weights.perimeter = objectiveFunction.perimeter;
    toOpt.obj_weights.resources = objectiveFunction.bitstream;
    toOpt.obj_weights.bitstream = objectiveFunction.wastedResources;
    toOpt.res_cost = {};
    toOpt.res_cost.LAB = 1;
    toOpt.res_cost.MK20 = 1;
    toOpt.res_cost.DSP = 1;
    toOpt.placement_generation_mode = objectiveFunction.genMode;
    toOpt.gurobi_params = {};
    toOpt.gurobi_params.MIPFocus = 1;
    toOpt.gurobi_params.TimeLimit = objectiveFunction.timeLimit;


    var json = JSON.stringify(toOpt);
    $.ajax({
        type: "POST",
        url: "optimizationScript.php",
        data: "optimize=" + json,
        success: function (result) {
        }});
}



