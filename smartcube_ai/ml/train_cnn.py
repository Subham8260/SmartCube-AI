"""
train_cnn.py — SmartCube AI  ML Training Script
================================================
Trains a CNN to classify Rubik's Cube sticker colors.
6 classes: white, yellow, red, orange, blue, green

Dataset structure:
    ml/dataset/train/white/   *.jpg
    ml/dataset/train/yellow/  *.jpg
    ...etc

Usage:
    python ml/train_cnn.py
    python ml/train_cnn.py --epochs 30 --lr 0.0005
"""

import os
import sys
import argparse
from typing import Optional

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATASET_DIR  = os.path.join(PROJECT_ROOT, "ml", "dataset")
TRAIN_DIR    = os.path.join(DATASET_DIR, "train")
VAL_DIR      = os.path.join(DATASET_DIR, "val")
MODEL_OUT    = os.path.join(PROJECT_ROOT, "backend", "color_cnn_model.h5")

CLASSES  = ["white", "yellow", "red", "orange", "blue", "green"]
IMG_SIZE = (32, 32)
BATCH    = 32


def parse_args():
    parser = argparse.ArgumentParser(description="Train SmartCube AI color classifier")
    parser.add_argument("--epochs",     type=int,   default=20)
    parser.add_argument("--lr",         type=float, default=0.001)
    parser.add_argument("--batch",      type=int,   default=BATCH)
    parser.add_argument("--no-augment", action="store_true")
    return parser.parse_args()


def build_model(num_classes=6):
    import tensorflow as tf
    from tensorflow.keras import layers, models, regularizers

    model = models.Sequential([
        layers.Conv2D(32, (3,3), padding="same", activation="relu",
                      input_shape=(*IMG_SIZE, 3),
                      kernel_regularizer=regularizers.l2(1e-4)),
        layers.BatchNormalization(),
        layers.MaxPooling2D((2,2)),

        layers.Conv2D(64, (3,3), padding="same", activation="relu",
                      kernel_regularizer=regularizers.l2(1e-4)),
        layers.BatchNormalization(),
        layers.MaxPooling2D((2,2)),

        layers.Conv2D(128, (3,3), padding="same", activation="relu"),
        layers.BatchNormalization(),
        layers.GlobalAveragePooling2D(),

        layers.Dense(128, activation="relu"),
        layers.Dropout(0.4),
        layers.Dense(num_classes, activation="softmax"),
    ], name="SmartCubeColorCNN")

    return model


def build_generators(args):
    import tensorflow as tf

    # Build augmentation params — avoid None values which crash older TF
    aug_params = {"rescale": 1.0/255}
    if not args.no_augment:
        aug_params["rotation_range"]    = 15
        aug_params["width_shift_range"] = 0.1
        aug_params["height_shift_range"]= 0.1
        aug_params["brightness_range"]  = [0.7, 1.3]
        aug_params["horizontal_flip"]   = True

    has_val_dir = os.path.isdir(VAL_DIR)
    if not has_val_dir:
        aug_params["validation_split"] = 0.15

    train_datagen = tf.keras.preprocessing.image.ImageDataGenerator(**aug_params)
    val_datagen   = tf.keras.preprocessing.image.ImageDataGenerator(rescale=1.0/255)

    common = dict(
        target_size=IMG_SIZE,
        batch_size=args.batch,
        class_mode="categorical",
        classes=CLASSES,
    )

    if has_val_dir:
        train_gen = train_datagen.flow_from_directory(TRAIN_DIR, **common)
        val_gen   = val_datagen.flow_from_directory(VAL_DIR, **common)
    else:
        train_gen = train_datagen.flow_from_directory(
            TRAIN_DIR, subset="training", **common)
        val_gen   = train_datagen.flow_from_directory(
            TRAIN_DIR, subset="validation", **common)

    return train_gen, val_gen


def train(args):
    import tensorflow as tf

    print(f"[train_cnn] TensorFlow {tf.__version__}")
    print(f"[train_cnn] Dataset : {TRAIN_DIR}")
    print(f"[train_cnn] Output  : {MODEL_OUT}")
    print(f"[train_cnn] Epochs={args.epochs}  LR={args.lr}  Batch={args.batch}")

    if not os.path.isdir(TRAIN_DIR):
        print(f"\n[ERROR] Dataset not found at: {TRAIN_DIR}")
        print("Create folders: ml/dataset/train/<color>/ and add sticker images.")
        sys.exit(1)

    train_gen, val_gen = build_generators(args)
    model = build_model(num_classes=len(CLASSES))
    model.summary()

    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=args.lr),
        loss="categorical_crossentropy",
        metrics=["accuracy"],
    )

    callbacks = [
        tf.keras.callbacks.EarlyStopping(
            monitor="val_accuracy", patience=5,
            restore_best_weights=True, verbose=1),
        tf.keras.callbacks.ReduceLROnPlateau(
            monitor="val_loss", factor=0.5, patience=3, verbose=1),
        tf.keras.callbacks.ModelCheckpoint(
            MODEL_OUT, monitor="val_accuracy",
            save_best_only=True, verbose=1),
    ]

    history = model.fit(
        train_gen,
        validation_data=val_gen,
        epochs=args.epochs,
        callbacks=callbacks,
    )

    best_acc = max(history.history.get("val_accuracy", [0]))
    print(f"\n[train_cnn] ✓ Model saved → {MODEL_OUT}")
    print(f"[train_cnn] Best val accuracy: {best_acc:.4f}")
    return history


if __name__ == "__main__":
    args = parse_args()
    train(args)