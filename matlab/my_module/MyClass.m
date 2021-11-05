classdef MyClass
   % Brief description of this class
   %
   % Longer description
   properties
      Value {mustBeNumeric} % Description of member of class
   end
   methods
      function r = roundOff(x)
         % Brief description of method
         % 
         % Longer description
         % 
         % Args:
         %  x (numeric): brief description of x 
         %
         % Returns:
         % (numeric): brief description of return variable
         r = x + obj.Value;
      end
   end
end