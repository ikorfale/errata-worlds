"""Stream of every Table 8 locality, read by hand from the OCR'd table (r.txt ~3570-3750): 'do' = ditto of the line above;
blank name lines whose A keeps rising are taken as the same stream (634, 622, 615, 576, 597, 593); 649 = Eidson Creek and
646 = Bell Creek from table 7; the unnamed Calfpasture block (627-653) as one stream; 630-632 one unnamed limestone stream."""
S = {}
def put(name, locs): [S.__setitem__(l, name) for l in locs.split()]
put('Eidson Creek', '649 648 647 639 638 637 634 635 636'); put('Bell Creek', '646 645 644'); put('limestone 630', '630 631 632')
put('Middle River', '624 623 622 615 575 576 589 588 592 591 597 593 596 619 617 599 652A 620 598')
put('North River', '652B 582 586 602 603 604 605 606A 606B')
put('Christians Creek', '650 657 621'); put('East Dry Branch', '569B 643 610 607 608 609 611 614')
put('Calfpasture', '627 628 629 656 662 655 654C 654B 654A 653'); put('Tye River', '579 578 580 577')
put('Gillis Falls', '692 691 689A 689B 693 694 690 695'); put('Butlers Branch', '696c 697c 698'); put('Mataponi Creek', '701 700')
