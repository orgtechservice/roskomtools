#!/bin/bash

fakeroot dpkg-deb --build rkn-load
fakeroot dpkg-deb --build rkn-check
fakeroot dpkg-deb --build rkn-parse
fakeroot dpkg-deb --build rkn-fakezonegen
