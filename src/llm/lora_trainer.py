#!/usr/bin/env python3
"""
LoRA Fine-Tuning Pipeline via Unsloth
Specializes models on wallet recovery patterns.
No stubs. No TODOs.
"""

import json
from pathlib import Path
from typing import Dict, List


class LoRATrainer:
    """
    Unsloth-based LoRA fine-tuning for Sec Guy.
    Trains on recovery patterns to improve semantic generation.
    """

    def __init__(self, base_model_path: str,
                 output_dir: str = "/opt/sec-guy/models/lora_adapters"):
        self.base_model_path = base_model_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def prepare_dataset(self, recovery_cases: List[Dict]) -> Path:
        """Convert recovery cases into Alpaca-format training data."""
        dataset = []
        for case in recovery_cases:
            instruction = case.get("instruction", "Generate password candidates")
            input_text = case.get("hints", "")
            output_text = json.dumps(case.get("result", {}))

            dataset.append({
                "instruction": instruction,
                "input": input_text,
                "output": output_text,
            })

        dataset_path = self.output_dir / "training_data.json"
        with open(dataset_path, "w") as f:
            json.dump(dataset, f, indent=2)
        return dataset_path

    def train(self, dataset_path: Path, adapter_name: str = "secguy_recovery",
              epochs: int = 3, batch_size: int = 2,
              learning_rate: float = 2e-4) -> Path:
        """
        Run Unsloth LoRA training.
        Requires unsloth and transformers to be installed.
        """
        try:
            from unsloth import FastLanguageModel
            from transformers import TrainingArguments
            from trl import SFTTrainer
            from datasets import load_dataset
        except ImportError:
            raise ImportError("unsloth not installed. Run: pip install unsloth")

        # Load model with Unsloth optimizations
        model, tokenizer = FastLanguageModel.from_pretrained(
            model_name=self.base_model_path,
            max_seq_length=2048,
            dtype=None,  # Auto-detect
            load_in_4bit=True,
        )

        # Add LoRA adapters
        model = FastLanguageModel.get_peft_model(
            model,
            r=16,
            target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                           "gate_proj", "up_proj", "down_proj"],
            lora_alpha=16,
            lora_dropout=0,
            bias="none",
            use_gradient_checkpointing="unsloth",
            random_state=3407,
        )

        # Load dataset
        dataset = load_dataset("json", data_files=str(dataset_path), split="train")

        # Training arguments
        training_args = TrainingArguments(
            output_dir=str(self.output_dir / adapter_name),
            num_train_epochs=epochs,
            per_device_train_batch_size=batch_size,
            gradient_accumulation_steps=4,
            learning_rate=learning_rate,
            logging_steps=10,
            optim="adamw_8bit",
            weight_decay=0.01,
            lr_scheduler_type="linear",
            seed=3407,
            report_to="none",
        )

        # Trainer
        trainer = SFTTrainer(
            model=model,
            tokenizer=tokenizer,
            train_dataset=dataset,
            dataset_text_field="text",
            max_seq_length=2048,
            args=training_args,
        )

        trainer.train()

        # Save adapter
        adapter_path = self.output_dir / adapter_name
        model.save_pretrained(str(adapter_path))
        tokenizer.save_pretrained(str(adapter_path))

        return adapter_path

    def merge_adapter(self, adapter_path: Path, output_path: Path) -> Path:
        """Merge LoRA adapter into base model for deployment."""
        try:
            from unsloth import FastLanguageModel
        except ImportError:
            raise ImportError("unsloth not installed")

        model, tokenizer = FastLanguageModel.from_pretrained(
            model_name=self.base_model_path,
            adapter_name=str(adapter_path),
            max_seq_length=2048,
        )

        model.save_pretrained_merged(str(output_path), tokenizer, save_method="merged_16bit")
        return output_path


if __name__ == "__main__":
    trainer = LoRATrainer("/opt/sec-guy/models/qwen2.5-coder-7b-q4_k_m.gguf")
    print("LoRA Trainer initialized.")
