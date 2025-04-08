import os
import json
import time
from openai import OpenAI
from openai.types.chat import ChatCompletion
from .config import get_openai_api_key, DEFAULT_MODEL
from .logger import CLIPSLogger

class AIIntegration:
    """Class to handle interactions with OpenAI API"""
    
    def __init__(self, logger=None):
        self.logger = logger or CLIPSLogger()
        self.client = None
        self.api_key = get_openai_api_key()
        self.initialize_client()
    
    def initialize_client(self, api_key=None):
        """Initialize OpenAI client with the given API key or the one from config"""
        if api_key:
            self.api_key = api_key
        
        if not self.api_key:
            return False
        
        try:
            self.client = OpenAI(api_key=self.api_key)
            return True
        except Exception as e:
            self.logger.log_error("Failed to initialize OpenAI client", 
                                 {"type": "api_error", "source": "initialize"}, e)
            return False
    
    def _make_api_call(self, messages, model=DEFAULT_MODEL, temperature=0.7, retries=1):
        """Make an API call to OpenAI with retries"""
        if not self.client:
            if not self.initialize_client():
                raise ValueError("OpenAI client not initialized. Please provide a valid API key.")
        
        error = None
        response = None
        endpoint = "ChatCompletion"
        
        for attempt in range(retries + 1):
            try:
                response = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature
                )
                error = None
                break
            except Exception as e:
                error = e
                if attempt < retries:
                    # Exponential backoff
                    wait_time = 2 ** attempt
                    self.logger.get_logger().warning(f"API call failed, retrying in {wait_time}s: {str(e)}")
                    time.sleep(wait_time)
                else:
                    self.logger.log_error("API call failed after retries", 
                                         {"type": "api_error", "source": endpoint}, e)
        
        # Log the API interaction
        self.logger.log_ai_interaction(
            endpoint=endpoint,
            prompt=json.dumps(messages),
            response=response.model_dump() if response else None,
            model=model,
            error=str(error) if error else None
        )
        
        if error:
            raise error
            
        return response
    
    def distill_variation_instructions(self, original_notes):
        """Distill user's original variation application instructions into concise, actionable form"""
        messages = [
            {"role": "developer", "content": "You are helping distill a copywriter's instructions for AI-generated variations. "
             "Transform their detailed notes into concise, actionable instructions that can be used directly in an AI prompt. "
             "Keep the core guidance but make it clearer and more directive. Be specific about goals, style guidelines, "
             "and how variations should differ."},
            {"role": "user", "content": f"Here are my original variation notes:\n\n{original_notes}\n\nPlease distill these into concise, actionable instructions for an AI prompt."}
        ]
        
        try:
            response = self._make_api_call(messages, temperature=0.3)
            return response.choices[0].message.content.strip()
        except Exception as e:
            self.logger.log_error("Failed to distill variation instructions", 
                                {"type": "api_error", "function": "distill_variation_instructions"}, e)
            return original_notes
    
    def interpret_feedback(self, original_copy, current_draft, feedback, instruction_set):
        """Interpret user feedback and suggest modifications to the instruction set"""
        # Prepare a simplified version of the instruction set for the API call
        simplified_instructions = {}
        for category, value in instruction_set.items():
            if category in ['partner_name', 'distilled_variation_instructions', 'marker_instructions', 'tone_other_prompts']:
                simplified_instructions[category] = value
        
        messages = [
            {"role": "developer", "content": "You are an expert copy editor analyzing feedback on a draft. "
             "Your task is to interpret the user's feedback and suggest specific changes to the instruction set "
             "that would address the feedback and improve the next draft. Focus on actionable modifications to "
             "one or more instruction categories."},
            {"role": "user", "content": f"Original Copy Template:\n\n{original_copy}\n\n"
             f"Current Draft:\n\n{current_draft}\n\n"
             f"User Feedback:\n\n{feedback}\n\n"
             f"Current Instruction Set Categories:\n\n{json.dumps(simplified_instructions, indent=2)}\n\n"
             f"Based on the feedback, which instruction category(ies) should be modified, and how? "
             f"Return your answer as a JSON object with the category names as keys and the suggested new values as values. "
             f"Only include categories that need changes."}
        ]
        
        try:
            response = self._make_api_call(messages, temperature=0.4)
            content = response.choices[0].message.content.strip()
            
            # Try to extract JSON from the response
            try:
                # Find JSON content if it's embedded in other text
                json_match = re.search(r'\{[\s\S]*\}', content)
                if json_match:
                    content = json_match.group(0)
                
                instruction_updates = json.loads(content)
                return instruction_updates
            except (json.JSONDecodeError, AttributeError):
                self.logger.log_error("Failed to parse JSON from feedback interpretation", 
                                    {"type": "parsing_error", "content": content})
                return {}
                
        except Exception as e:
            self.logger.log_error("Failed to interpret feedback", 
                                {"type": "api_error", "function": "interpret_feedback"}, e)
            return {}
    
    def generate_draft(self, original_copy, instructions, variation_levels=None, json_data=None):
        """Generate a single draft based on original copy, instructions, and variation data"""
        # Prepare the prompt with all the necessary components
        prompt_parts = [
            "You are an expert copywriter creating personalized marketing content for college enrollment.",
            "\n## Original Copy Template:\n",
            original_copy,
            "\n## Instructions:\n"
        ]
        
        # Add partner name if available
        if instructions.get('partner_name'):
            prompt_parts.append(f"Target Institution: {instructions['partner_name']}")
        
        # Add distilled variation instructions
        if instructions.get('distilled_variation_instructions'):
            prompt_parts.append(f"\nVariation Strategy:\n{instructions['distilled_variation_instructions']}")
        
        # Add variation levels for this draft
        if variation_levels:
            prompt_parts.append("\n## Variation Levels for this Draft:\n")
            for var_name, level in variation_levels.items():
                prompt_parts.append(f"- {var_name}: {level}")
        
        # Add marker instructions
        if instructions.get('marker_instructions'):
            prompt_parts.append(f"\n## Marker Instructions:\n{instructions['marker_instructions']}")
            prompt_parts.append("When you encounter text in {{DOUBLE_BRACES}} format, apply the corresponding marker instructions.")
        
        # Add JSON data if available and relevant
        if json_data and variation_levels:
            field_of_interest_var = next((var for var in variation_levels if var.lower() in ['field of interest', 'program', 'major']), None)
            if field_of_interest_var and 'data' in variation_levels[field_of_interest_var]:
                cip_code = variation_levels[field_of_interest_var]['data']
                program_data = json_data.get('programs', {}).get('by_cip_code', {}).get(cip_code, [])
                club_data = json_data.get('clubs', {}).get('by_cip_code', {}).get(cip_code, [])
                
                if program_data or club_data:
                    prompt_parts.append("\n## Available Content Data:\n")
                    
                    if program_data:
                        prompt_parts.append("Program Data:")
                        prompt_parts.append(json.dumps(program_data, indent=2))
                    
                    if club_data:
                        prompt_parts.append("Club Data:")
                        prompt_parts.append(json.dumps(club_data, indent=2))
                    
                    prompt_parts.append("Integrate this data where appropriate when filling in {{MARKERS}}.")
        
        # Add tone and other final prompts
        if instructions.get('tone_other_prompts'):
            prompt_parts.append(f"\n## Tone & Style:\n{instructions['tone_other_prompts']}")
        
        # Final guidance
        prompt_parts.append("\n## Final Guidelines:\n"
                         "1. Preserve the overall structure of the original copy."
                         "2. Replace all {{MARKERS}} with appropriate content based on the variation levels and instructions."
                         "3. Ensure the copy feels natural, engaging, and personalized to the specified variation levels."
                         "4. Output ONLY the final copy, with no explanations or notes.")
        
        # Combine all parts into the final prompt
        full_prompt = "\n".join(prompt_parts)
        
        messages = [
            {"role": "developer", "content": "You are an expert copywriter for college enrollment marketing."},
            {"role": "user", "content": full_prompt}
        ]
        
        try:
            response = self._make_api_call(messages, temperature=0.7)
            return response.choices[0].message.content.strip()
        except Exception as e:
            self.logger.log_error("Failed to generate draft", 
                                {"type": "api_error", "function": "generate_draft"}, e)
            return f"Error generating draft: {str(e)}"
