#!/bin/bash

fakeroot dpkg-deb --build rkn-load
fakeroot dpkg-deb --build rkn-check
