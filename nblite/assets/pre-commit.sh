#!/bin/sh

if [ "$NBL_DISABLE_PC" = "true" ]; then
    exit
fi

if [ "$NBL_DISABLE_PC_CLEAN" != "true" ]; then
    nbl clean
fi

if [ "$NBL_DISABLE_PC_EXPORT" != "true" ]; then
    nbl export
fi

if [ "$NBL_DISABLE_PC_VALIDATE" != "true" ]; then
    nbl validate-staging
fi
